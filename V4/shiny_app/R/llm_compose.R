# =====================================================================
# AEGIS V4.6R2 | llm_compose.R | Local deterministic composition engine
# ---------------------------------------------------------------------
# PURPOSE
#   Turn a governed evidence pack + a user question into a freshly
#   COMPOSED answer (executive paragraphs), adapting to the intent of
#   the question. This is NOT a stored .md echo: the paragraphs are
#   assembled at runtime from the evidence facts, selected and phrased
#   by question intent, then passed through a governed validator.
#
# GOVERNANCE (hard invariants)
#   - Local-first. NO real LLM, NO Azure, NO external API, NO network.
#   - NO SQL, NO model refresh, NO forecast compute.
#   - Reads only the in-memory governed response (already sourced from
#     the read-only V4.4 evidence). It never mutates anything.
#   - Champion language and governed wording are preserved; a sanitizer
#     acts as a safety net for forbidden language.
#   - The answer is always bounded to the evidence available for the
#     current section; open-ended claims are refused.
#
# NOTE
#   A real open-ended generator (local Ollama / Azure OpenAI) is a
#   separate, gated phase (V4.6L / V4.9). This engine gives the
#   "reasons over the evidence" experience while staying fully offline.
# =====================================================================

# ---------------------------------------------------------------------
# Small text utilities (reuse .llm_or / .llm_chr_vec from llm_explain.R)
# ---------------------------------------------------------------------
.comp_lower1 <- function(s) {
  s <- trimws(.llm_or(s, ""))
  if (nzchar(s)) substr(s, 1, 1) <- tolower(substr(s, 1, 1))
  sub("\\.$", "", s)
}

.comp_first <- function(v) {
  v <- v[nzchar(v)]
  if (length(v)) v[[1]] else ""
}

# Join a set of fact sentences into one flowing paragraph.
.comp_prose <- function(facts, max_n = 3) {
  facts <- facts[nzchar(facts)]
  if (length(facts) == 0) return("")
  facts <- facts[seq_len(min(length(facts), max_n))]
  facts <- vapply(facts, function(x) {
    x <- trimws(x)
    if (nzchar(x) && !grepl("[.!?]$", x)) x <- paste0(x, ".")
    x
  }, character(1))
  paste(facts, collapse = " ")
}

# ---------------------------------------------------------------------
# Governed sanitizer (safety net). The source evidence is already
# sanitized; this only guards against forbidden tokens leaking into
# composed text. It must never alter the champion name.
# ---------------------------------------------------------------------
.comp_sanitize <- function(s) {
  s <- .llm_or(s, "")
  if (!nzchar(s)) return(s)
  s <- gsub("\\bpromoted\\b", "retained", s, ignore.case = TRUE)
  s <- gsub("\\bpromote\\b",  "retain",   s, ignore.case = TRUE)
  s <- gsub("\\bwinner\\b",   "leading candidate", s, ignore.case = TRUE)
  s <- gsub("\\bthe best\\b", "the leading", s, ignore.case = TRUE)
  s
}

# ---------------------------------------------------------------------
# Fact base: split the governed claims into content / process / numeric.
# Content claims -> the visible facts of the section.
# Process claims (ids *_9x or pack_metadata/candidate_claims fields) ->
# governance/methodology facts used to explain "the process".
# ---------------------------------------------------------------------
.comp_factbase <- function(resp) {
  claims <- resp$claims_traceability
  content <- character(0)
  process <- character(0)

  if (!is.null(claims) && length(claims)) {
    for (c in claims) {
      txt <- trimws(.llm_or(c$claim, ""))
      if (!nzchar(txt)) next
      id     <- .llm_or(c$claim_id, "")
      fields <- .llm_or(c$evidence_fields, "")
      is_meta <- grepl("9[0-9]$", id) ||
                 grepl("pack_metadata|candidate_claims", fields)
      if (is_meta) process <- c(process, txt) else content <- c(content, txt)
    }
  }
  if (length(content) == 0) content <- .llm_chr_vec(resp$what_the_evidence_says)

  numeric <- content[grepl("[0-9]", content)]
  list(
    content = unique(content),
    process = unique(process),
    numeric = unique(numeric)
  )
}

# Substantive limitations only (drop the generic "LLM explains ..." line).
.comp_caveats <- function(resp, max_n = 3) {
  l <- .llm_chr_vec(resp$limitations)
  l <- l[!grepl("^LLM explains", l)]
  if (length(l) > max_n) l <- l[seq_len(max_n)]
  l
}

# Facts most relevant to a "what changed" question.
.comp_change_facts <- function(content) {
  content[grepl(
    "not re-?fit|not changed|retained|none advanced|0 candidates|no change",
    content, ignore.case = TRUE)]
}

# Facts most relevant to a comparison/ranking question.
.comp_compare_facts <- function(content) {
  m <- content[grepl(
    "ratio|closest|rank|challenger|advanced|\\dx",
    content, ignore.case = TRUE)]
  if (length(m)) m else content
}

# ---------------------------------------------------------------------
# Intent detection from the user's question.
# ---------------------------------------------------------------------
.comp_intent <- function(question) {
  ql <- tolower(trimws(.llm_or(question, "")))
  if (!nzchar(ql)) return("default")

  if (grepl(paste0(
        "should (i|we|they)|recommend|do you (think|recommend)|\\bpromote\\b|",
        "replace the champion|which model should|\\bpredict\\b|guarantee|",
        "\\bexact\\b|\\binvest\\b|\\bbuy\\b|make the decision"), ql))
    return("bounded")

  # Comparison/ranking is checked before "process" so that questions like
  # "how does X compare to Y" are not swallowed by the generic "how does".
  if (grepl("compar|closest|challenger|\\brank|versus|\\bvs\\b|against|distance|gap", ql))
    return("compare")

  if (grepl(paste0(
        "accura|\\bmase\\b|\\brmsse\\b|number|metric|how good|how many|",
        "score|ratio|count|figure"), ql))
    return("numeric")

  if (grepl("chang|different|move|update|since|what happened", ql))
    return("changed")

  if (grepl("risk|danger|concern|worry|wrong|fail|caution|limitation", ql))
    return("risk")

  if (grepl("attention|watch|focus|look at|notice|\\bpay\\b|careful|aware", ql))
    return("attention")

  if (grepl(paste0(
        "process|how (does|is|are|do|did)|how it works|methodolog|pipeline|",
        "\\bstep|where.*(come|from)|how.*(produced|generated|computed)|",
        "explain the process|walk me through"), ql))
    return("process")

  if (grepl("take ?away|summar|\\bkey\\b|\\bmain\\b|overall|tl;dr|bottom line", ql))
    return("takeaway")

  "default"
}

# ---------------------------------------------------------------------
# Compose the answer. Returns a list of composed, validated strings.
#   lead        : direct answer to the question (shown only when asked)
#   exec        : Executive summary paragraph (intent-framed synthesis)
#   evidence    : What the evidence says paragraph (intent-selected facts)
#   why         : Why it matters paragraph (intent-aware opener)
#   limitations : up to 3 substantive caveats
#   bounded     : TRUE if the question was outside the evidence
#   intent      : detected intent (for traceability)
# ---------------------------------------------------------------------
.comp_answer <- function(resp, question) {
  fb     <- .comp_factbase(resp)
  intent <- .comp_intent(question)
  caveats <- .comp_caveats(resp, 3)
  why_src <- .llm_or(resp$why_it_matters, "")

  content <- fb$content
  process <- fb$process
  numeric <- if (length(fb$numeric)) fb$numeric else content

  # --- evidence fact set + executive framing, by intent ----------------
  if (intent == "process") {
    ev_facts  <- if (length(process)) process else content
    exec <- paste0(
      "This explanation is produced under governed, evidence-only conditions: ",
      .comp_prose(process, 2))
    lead <- paste0(
      "Here is how this section is produced. ",
      .comp_first(process))
    why <- paste0(
      "Showing the process matters because every statement here can be traced ",
      "back to a recorded artifact, and nothing is inferred beyond the evidence.")
  } else if (intent == "numeric") {
    ev_facts <- numeric
    exec <- paste0("The recorded figures are: ", .comp_prose(numeric, 3))
    lead <- paste0("On the recorded numbers, ", .comp_lower1(.comp_first(numeric)), ".")
    why  <- paste0("These figures matter as evidence of record only. ",
                   .comp_first_sentence(why_src))
  } else if (intent == "risk") {
    ev_facts <- if (length(caveats)) caveats else content
    exec <- paste0("The main caveats to keep in mind are: ", .comp_prose(caveats, 3))
    lead <- paste0("The point to be careful about is ",
                   .comp_lower1(.comp_first(if (length(caveats)) caveats else content)), ".")
    why  <- paste0("These caveats matter so the section is read as supporting ",
                   "evidence, not as an automated decision.")
  } else if (intent == "changed") {
    chg <- .comp_change_facts(content)
    ev_facts <- if (length(chg)) chg else content
    exec <- if (length(chg)) {
      paste0("Regarding change, ", .comp_lower1(.comp_first(chg)), ". ",
             .comp_prose(chg[-1], 2))
    } else {
      paste0("Regarding change, the governed evidence for this section does not ",
             "record a change. ", .comp_prose(content, 2))
    }
    lead <- paste0("On what changed: ",
                   if (length(chg)) .comp_lower1(.comp_first(chg))
                   else "the evidence does not record a change for this section", ".")
    why  <- .comp_first_sentence(why_src)
  } else if (intent == "compare") {
    cmp <- .comp_compare_facts(content)
    ev_facts <- cmp
    exec <- paste0("On the comparison, ", .comp_prose(cmp, 3))
    lead <- paste0("On the comparison, ", .comp_lower1(.comp_first(cmp)), ".")
    why  <- .comp_first_sentence(why_src)
  } else if (intent == "attention") {
    ev_facts <- content
    exec <- paste0("The key things to keep an eye on are: ",
                   .comp_prose(c(content, caveats), 3))
    lead <- paste0("What you should pay attention to is ",
                   .comp_lower1(.comp_first(content)), ".")
    why  <- .comp_first_sentence(why_src)
  } else if (intent == "takeaway") {
    ev_facts <- content
    exec <- paste0("In short, ", .comp_prose(content, 2))
    lead <- paste0("The main takeaway is that ", .comp_lower1(.comp_first(content)), ".")
    why  <- .comp_first_sentence(why_src)
  } else if (intent == "bounded") {
    ev_facts <- content
    exec <- paste0("Using only the governed evidence available for this section, ",
                   .comp_prose(content, 3))
    lead <- paste0("I can only answer using the governed evidence available for ",
                   "this section. Based on that evidence, ",
                   .comp_lower1(.comp_first(content)), ".")
    why  <- .comp_first_sentence(why_src)
  } else { # default (no question / generic)
    ev_facts <- content
    exec <- paste0("Based on the governed artifacts currently available, ",
                   .comp_prose(content, 3))
    lead <- ""  # no asked-lead when there is no question
    why  <- .comp_first_sentence(why_src)
  }

  evidence <- .comp_prose(ev_facts, 4)
  if (!nzchar(evidence)) evidence <- .comp_prose(content, 4)
  if (!nzchar(why))      why      <- why_src

  list(
    lead        = .comp_sanitize(trimws(lead)),
    exec        = .comp_sanitize(trimws(exec)),
    evidence    = .comp_sanitize(trimws(evidence)),
    why         = .comp_sanitize(trimws(why)),
    limitations = vapply(caveats, .comp_sanitize, character(1)),
    bounded     = identical(intent, "bounded"),
    intent      = intent
  )
}

# First sentence helper (kept local so this file is self-sufficient).
.comp_first_sentence <- function(s) {
  s <- trimws(.llm_or(s, ""))
  if (!nzchar(s)) return(s)
  m <- regexpr("[^.]*\\.", s)
  if (m > 0) trimws(regmatches(s, m)) else s
}
