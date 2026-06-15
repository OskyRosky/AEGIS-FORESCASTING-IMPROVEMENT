start.time <- Sys.time()

########################################################################################
#                                                                                      #
#                                                                                      #
#       Extracción + transformación + creacción de tablas (datamart)                   #
#                                                                                      #
#                                                                                      #
########################################################################################

###############
#   General   #
###############


#############################
#   Estructura del código   #  
#############################

# 0. Establecimiento de la configuración general del espacio de trabajo.
#
# 1. Importación de los archivos y otros referentes a los ingresos.
#
# 2. Ciertas modificaciones previar generales.
#
# 3. Unión + Transformación de ingresos mensuales + anuales
#
# 4. Creación de las principales tablas.
#
# 5. Exportación de los tablas con información.


#####
# 0 #  
##################################################################################################
##################################################################################################
#                         Establecimiento de la  configuración general                           #
##################################################################################################
##################################################################################################

######################
# Opciones generales #
###################### 

options(encoding="utf-8")
options(scipen=999)


###############
#  Librerías  #
###############


suppressMessages(library(readxl))
suppressMessages(library(dplyr))
suppressMessages(library(DT))
suppressMessages(library(plyr))
suppressMessages(library(readr))
suppressMessages(library(tidyr))
suppressMessages(library(stringr))
suppressMessages(library(highcharter))
suppressMessages(library(RcppRoll))
suppressMessages(library(openxlsx))


#####################################################
#####################################################
#         Parámetros: datos + dashboard             #
#####################################################
#####################################################

#############
#  Millones #
#############

Millones <- 1000000

#####################################################
#####################################################
#         Parámetros: datos + dashboard             #
#####################################################
#####################################################

#############
#  Millones #
#############

Millones <- 1000000

################################
#  Delimitación años análisis  #
################################

Anos_analisis <- 2007

####################
#  Años referencia #
####################

#Ano_actual    <- 2021
#Ano_pasado_1  <- 2020  
#Ano_pasado_2  <- 2019

Ano_actual    <- as.numeric(substr(Sys.Date(),1,4))
Ano_pasado_1  <- as.numeric(substr(Sys.Date(),1,4))-1  
Ano_pasado_2  <- as.numeric(substr(Sys.Date(),1,4))-2

####################
#  Mes referencia  #
####################

Mes_actual <- substr(Sys.Date(),6,7)

####################
#  Mes referencia  #
####################

Mes_actual <- substr(Sys.Date(),6,7)


#####
# 1 #  
##################################################################################################
##################################################################################################
##################################################################################################
#                              Importación de los ingresos                                       #
##################################################################################################
##################################################################################################
##################################################################################################

#############################
#    Ingresos 2007-2021     #
#############################

setwd("C:/Users/regla.fiscal/Desktop/Datos/SIGAF/Consolidados/Ingresos/Final")

ingresos_anual <- suppressWarnings(
  
                read_excel("Ingresos_a.xlsx", 
                             col_types = c("numeric", "numeric", "text", 
                                         "text", "text", "text", "numeric", 
                                         "numeric", "numeric", "numeric", 
                                         "numeric", "text", "text", "text", 
                                         "text", "text", "text", "text", "text", 
                                         "text", "text", "text", "text", "text", 
                                         "text", "text", "text", "text", "numeric", 
                                         "text", "numeric", "numeric", "numeric", 
                                         "numeric", "numeric", "numeric", 
                                         "numeric", "numeric", "numeric", 
                                         "numeric", "numeric", "numeric"))
  
  ) # ingresos_2007_2021

ingresos_anual_s0 <- suppressWarnings(read_excel("Ingresos_a_s0.xlsx")) # ingresos_2007_2021

ingresos_mensual <- suppressWarnings(read_excel("Ingresos_m.xlsx")) # ingresos_2007_2021

Impuestos <- suppressWarnings(read_excel("Impuestos.xlsx")) # ingresos_2007_2021

PIB <- suppressWarnings(read_excel("PIB.xlsx")) # ingresos_2007_2021


########################################################################################################################
########################################################################################################################
#                                            Creación de tablas                                                        #
########################################################################################################################
########################################################################################################################


###############################
#  Evolución de los ingresos  #
###############################

# Anual

tabla_1 <- ingresos_anual %>%
  dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
  dplyr::group_by(Año) %>% 
  dplyr::summarise (  "Actual"    = sum(`Presupuesto actual`, na.rm = TRUE),
                      "Ajustado"   = sum(`Presupuesto ajustado`, na.rm = TRUE),
                      "Ajustado especial"   = sum(`Presupuesto ajustado especial`, na.rm = TRUE),
                      "Acumulado"  = sum(`Acumulado`, na.rm = TRUE),
                      "Inicial" = sum(`Presupuesto inicial`,na.rm=TRUE),
                      ) %>% as.data.frame()


# Mensual

tabla_2 <-  ingresos_mensual %>%
                 dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
                 dplyr::group_by(Año, mes.cod, mes) %>% 
                 dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE))  %>%
                 mutate(
                   Fecha = paste(Año,mes,sep ="-"))    %>%  
                dplyr::filter(Ingresos>0)
  

tabla_2 <- as.data.frame(tabla_2)

Ingresos_mensual <- tabla_2

Ingresos_mensual <- Ingresos_mensual %>%
  dplyr::mutate(
    Ingresos = round(Ingresos/Millones,1)
  )

# Ingresos_mensual  <- highchart() %>% 
#   hc_title(text = "",
#            margin = 20, align = "center",
#            style = list(color = "#129", useHTML = TRUE)) %>% 
#   hc_subtitle(text = "",
#               align = "right",
#               style = list(color = "#634", fontWeight = "bold")) %>%
#   hc_credits(enabled = TRUE, # add credits
#              text = "" # href = "www.cgr.go.cr"
#   ) %>%
#   hc_legend(align = "left", verticalAlign = "top",
#             layout = "vertical", x = 0, y = 100) %>%
#   hc_exporting(enabled = TRUE) %>% 
#   hc_xAxis(categories = Ingresos_mensual$Fecha) %>% 
#   hc_add_series(name = "Ingresos", data = Ingresos_mensual$Ingresos) %>% 
#   hc_chart(zoomType = "xy")
# 
# Ingresos_mensual


tabla_2_var <- tabla_2 %>% mutate( 
                                   var.Ingresos = round((Ingresos/lag(Ingresos,n = 12)-1)*100,2),
                                   acum_12 = roll_sum(Ingresos, 12, align = "right", fill = NA),
                                   var.acum_12  = round((acum_12/lag(acum_12,n = 12)-1)*100,1)
                                 )

tabla_2_var <- tabla_2_var  %>% 
               dplyr::group_by(Año) %>% 
               dplyr::mutate(  cum_ano_Ingresos     = cumsum(Ingresos)
                              )
tabla_2_var <- data.frame(tabla_2_var)

tabla_2_var <-  tabla_2_var %>% dplyr::mutate(
                                       var.cum_ano_Ingresos =  round((cum_ano_Ingresos/lag(cum_ano_Ingresos,n = 12)-1)*100,1) 
                                       )

# datos <- datos %>% dplyr::group_by(Año)  %>% dplyr::mutate(
#   cum_ano_Ingresos     = cumsum(Ingresos)
# )  
# datos <- data.frame(datos)
# 
# datos <- datos %>% dplyr::mutate(var.cum_ano_Ingresos =  round((cum_ano_Ingresos/lag(cum_ano_Ingresos,n = 12)-1)*100,1) )


########################################################################################################################
########################################################################################################################
#                                         Principales indicadores                                                      #
########################################################################################################################
########################################################################################################################

#####################
# Ingresos globales #
#####################

#Recaudación acumulada.

indicador.1 <- ingresos_anual %>%
  dplyr::filter(Año==Ano_actual) %>% 
  dplyr::filter(cod_subclase==11)  %>% 
  dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
  dplyr::summarise ("Ingresos"  = sum(Acumulado, na.rm = TRUE)) 

#Carga tributaria

ind.PIB <- PIB %>% 
  dplyr::filter(Ejercicio==Ano_actual) %>% 
  dplyr::select('PIB corriente precios de mercado')

ind.PIB <-ind.PIB*1000000

indicador.2 <- round(indicador.1/ind.PIB*100,1)


# Ejecución

Presu.ajustado <- ingresos_anual %>%
  dplyr::filter(Año==2021) %>% 
  dplyr::filter(cod_subclase==11)  %>% 
  dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
  dplyr::summarise ("Presupuesto ajustado"  = sum(`Presupuesto ajustado`, na.rm = TRUE)) 

indicador.3 <- round((indicador.1/Presu.ajustado)*100,1)


#Var% acumulado a 12 meses

indicador.4 <-  tabla_2_var  %>% select(var.Ingresos) %>% slice(c( n()))
                                                  
#Var% interanual (mensual y acumulada)

indicador.5 <- tabla_2_var  %>% select(var.acum_12) %>% slice(c( n()))

# Variación acumulada al mes

indicador.6 <- tabla_2_var  %>% select(var.cum_ano_Ingresos) %>% slice(c( n()))

################################################# 
#      Evolución de los ingresos mensuales      #
#################################################

#####
#  Recaudación acumulada
#######



tabla.evo.mensual.1 <- ingresos_mensual %>%
  dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
  dplyr::filter(cod_subclase==11)  %>% 
  dplyr::group_by(Año, mes.cod, mes) %>% 
  dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE))  %>% 
  dplyr::filter(Ingresos>=100)  %>%
  dplyr:: mutate(
    Fecha = paste(Año,mes,sep ="-")) 



tabla.evo.mensual.1_acum <- tabla.evo.mensual.1  %>% 
  dplyr::group_by(Año) %>% 
  dplyr::mutate(
    cum_ingresos = cumsum(Ingresos) 
  )







#  t.e.m.1   <- highchart() %>% 
#                               hc_title(text = "",
#                                        margin = 20, align = "center",
#                                        style = list(color = "#129", useHTML = TRUE)) %>% 
#                               hc_subtitle(text = "",
#                                           align = "right",
#                                           style = list(color = "#634", fontWeight = "bold")) %>%
#                               hc_credits(enabled = TRUE, # add credits
#                                          text = "" # href = "www.cgr.go.cr"
#                               ) %>%
#                               hc_legend(align = "left", verticalAlign = "top",
#                                         layout = "vertical", x = 0, y = 100) %>%
#                               hc_exporting(enabled = TRUE) %>% 
#                               hc_xAxis(categories = tabla.evo.mensual.1_acum$Fecha) %>% 
#                               hc_add_series(name = "Ingresos", data = tabla.evo.mensual.1_acum$cum_ingresos) %>% 
#                               hc_yAxis(title = list(text = "Millones de colones"), labels = list(format = "{value}"))%>% 
#                               hc_xAxis(title = list(text = "Año-mes") )  %>% 
#                               hc_chart(zoomType = "xy")
#  
#  
#  t.e.m.1

###########################
#     Carga tributaria    #
###########################

PIB  <- PIB %>%   dplyr::mutate(
  `PIB corriente precios de mercado` = `PIB corriente precios de mercado`*1000000
) %>% 
  dplyr::rename(
    
    Año = Ejercicio
  ) %>% dplyr::filter(Año >= 2007)



tabla.evo.mensual.2_acum <- tabla.evo.mensual.1_acum %>%  
  dplyr::full_join(PIB)  %>% 
  dplyr::mutate(
    `Carga tributaria` =  round(cum_ingresos/`PIB corriente precios de mercado`*100,1)
  )



#  t.e.m.2   <- highchart() %>% 
#    hc_title(text = "",
#             margin = 20, align = "center",
#             style = list(color = "#129", useHTML = TRUE)) %>% 
#    hc_subtitle(text = "",
#                align = "right",
#                style = list(color = "#634", fontWeight = "bold")) %>%
#    hc_credits(enabled = TRUE, # add credits
#               text = "" # href = "www.cgr.go.cr"
#    ) %>%
#    hc_legend(align = "left", verticalAlign = "top",
#              layout = "vertical", x = 0, y = 100) %>%
#    hc_exporting(enabled = TRUE) %>% 
#    hc_xAxis(categories = tabla.evo.mensual.2_acum$Fecha) %>% 
#    hc_add_series(name = "Carga tributaria", data = tabla.evo.mensual.2_acum$`Carga tributaria`) %>% 
#    hc_yAxis(title = list(text = "Millones de colones"), labels = list(format = "{value}"))%>% 
#    hc_xAxis(title = list(text = "Año-mes") )  %>% 
#    hc_chart(zoomType = "xy")
#  t.e.m.2
# 

##########################
#  Ejecución  mensual 
###########################


# Presu.ajustado <- ingresos_anual %>%
#   dplyr::filter(Año==2021) %>% 
#   dplyr::filter(cod_subclase==11)  %>% 
#   dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
#   dplyr::summarise ("Presupuesto ajustado"  = sum(`Presupuesto ajustado`, na.rm = TRUE)) 
# 
# indicador.3 <- round((indicador.1/Presu.ajustado)*100,1)



tabla.evo.mensual.3 <- ingresos_mensual %>%
  dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
  dplyr::filter(cod_subclase==11)  %>% 
  dplyr::group_by(Año, mes.cod, mes) %>% 
  dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE),
                    "Presu_ajustado" = sum(`Presupuesto ajustado`, na.rm = TRUE),
                    
  )  %>% 
  dplyr::filter(Ingresos>=100)  %>%
  dplyr:: mutate(
    Fecha = paste(Año,mes,sep ="-")) 



tabla.evo.mensual.3_acum <- tabla.evo.mensual.3  %>% 
  dplyr::group_by(Año) %>% 
  dplyr::mutate(
    cum_ingresos = cumsum(Ingresos),
    `Ejecucion` =  round(cum_ingresos/`Presu_ajustado`*100,1)
    
    
    #     `Ejecución mensual` = round((cum_ingresos/`Presupuesto ajustado`)*100,1
  )

#   t.e.m.3   <- highchart() %>% 
#     hc_title(text = "",
#              margin = 20, align = "center",
#              style = list(color = "#129", useHTML = TRUE)) %>% 
#     hc_subtitle(text = "",
#                 align = "right",
#                 style = list(color = "#634", fontWeight = "bold")) %>%
#     hc_credits(enabled = TRUE, # add credits
#                text = "" # href = "www.cgr.go.cr"
#     ) %>%
#     hc_legend(align = "left", verticalAlign = "top",
#               layout = "vertical", x = 0, y = 100) %>%
#     hc_exporting(enabled = TRUE) %>% 
#     hc_xAxis(categories = tabla.evo.mensual.3_acum$Fecha) %>% 
#     hc_add_series(name = "% Ejecución", data = tabla.evo.mensual.3_acum$`Ejecución`) %>% 
#     hc_yAxis(title = list(text = "Millones de colones"), labels = list(format = "{value}"))%>% 
#     hc_xAxis(title = list(text = "Año-mes") )  %>% 
#     hc_chart(zoomType = "xy")
#   t.e.m.3
# 



# ###############################
# #  Ingresos por Clasificador  #
# ###############################
# 
# ###############
# #     Clase   #
# ###############
# 
# tabla_clasi_c_1_1 <- ingresos_mensual  %>%
#                        dplyr::filter(Nivel==1)%>%
#                        dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
#                        dplyr::group_by(Año, Descripcion, mes.cod, mes) %>%
#                        dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE)) %>%
#                        mutate(
#                          Fecha = paste(Año,mes,sep ="-")) %>%
#                        dplyr::arrange(Descripcion, Año)  %>% 
#                        pivot_wider(
#                          names_from = Descripcion,
#                          values_from = Ingresos
#                        )  
#                          
# 
# ###############
# # Subclase
# ###############
# 
# tabla_clasi_c_2_1 <- ingresos_mensual  %>%
#                                   dplyr::filter(Nivel==2)%>%
#                                   dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
#                                   dplyr::group_by(Año, Descripcion, mes.cod, mes) %>%
#                                   dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE)) %>%
#                                   mutate(
#                                     Fecha = paste(Año,mes,sep ="-")) %>%
#                                   dplyr::arrange(Descripcion, Año)  %>% 
#                                   pivot_wider(
#                                     names_from = Descripcion,
#                                     values_from = Ingresos
#                                   )  
# 
# ###############
# # Grupo
# ###############
# 
# tabla_clasi_c_3_1 <- ingresos_mensual  %>%
#   dplyr::filter(Nivel==3)%>%
#   dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
#   dplyr::group_by(Año, Descripcion, mes.cod, mes) %>%
#   dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE)) %>%
#   mutate(
#     Fecha = paste(Año,mes,sep ="-")) %>%
#   dplyr::arrange(Descripcion, Año)  %>% 
#   pivot_wider(
#     names_from = Descripcion,
#     values_from = Ingresos
#   )  
# 
# ###############
# # Subgrupo
# ###############
# 
# tabla_clasi_c_4_1 <- ingresos_mensual  %>%
#   dplyr::filter(Nivel==4)%>%
#   dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
#   dplyr::group_by(Año, Descripcion, mes.cod, mes) %>%
#   dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE)) %>%
#   mutate(
#     Fecha = paste(Año,mes,sep ="-")) %>%
#   dplyr::arrange(Descripcion, Año)  %>% 
#   pivot_wider(
#     names_from = Descripcion,
#     values_from = Ingresos
#   )  
# 
# ###############
# # Partida
# ###############
# 
# tabla_clasi_c_5_1 <- ingresos_mensual  %>%
#   dplyr::filter(Nivel==5)%>%
#   dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
#   dplyr::group_by(Año, Descripcion, mes.cod, mes) %>%
#   dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE)) %>%
#   mutate(
#     Fecha = paste(Año,mes,sep ="-")) %>%
#   dplyr::arrange(Descripcion, Año)  %>% 
#   pivot_wider(
#     names_from = Descripcion,
#     values_from = Ingresos
#   )  
# 
# ###############
# # Subpartida
# ###############
# 
# tabla_clasi_c_6_1 <- ingresos_mensual  %>%
#   dplyr::filter(Nivel==6)%>%
#   dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
#   dplyr::group_by(Año, Descripcion, mes.cod, mes) %>%
#   dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE)) %>%
#   mutate(
#     Fecha = paste(Año,mes,sep ="-")) %>%
#   dplyr::arrange(Descripcion, Año)  %>% 
#   pivot_wider(
#     names_from = Descripcion,
#     values_from = Ingresos
#   )  
# 
# ###############
# # Renglón
# ###############
# 
# tabla_clasi_c_7_1 <- ingresos_mensual  %>%
#   dplyr::filter(Nivel==7)%>%
#   dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
#   dplyr::group_by(Año, Descripcion, mes.cod, mes) %>%
#   dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE)) %>%
#   mutate(
#     Fecha = paste(Año,mes,sep ="-")) %>%
#   dplyr::arrange(Descripcion, Año)  %>% 
#   pivot_wider(
#     names_from = Descripcion,
#     values_from = Ingresos
#   )  
# 
# ###############
# # Subrenglón
# ###############
# 
# tabla_clasi_c_8_1 <- ingresos_mensual  %>%
#   dplyr::filter(Nivel==8)%>%
#   dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
#   dplyr::group_by(Año, Descripcion, mes.cod, mes) %>%
#   dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE)) %>%
#   mutate(
#     Fecha = paste(Año,mes,sep ="-")) %>%
#   dplyr::arrange(Descripcion, Año)  %>% 
#   pivot_wider(
#     names_from = Descripcion,
#     values_from = Ingresos
#   )  
# 
# 
# #########################
# # Fuente de Financiación
# #########################
# 
# tabla_clasi_c_9_1 <- ingresos_mensual  %>%
#                                      dplyr::filter(Nivel==9)%>%
#                                      dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
#                                      dplyr::group_by(Año, Descripcion, mes.cod, mes) %>%
#                                      dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE)) %>%
#                                      mutate(
#                                        Fecha = paste(Año,mes,sep ="-")) %>%
#                                      dplyr::arrange(Descripcion, Año)  %>% 
#                                      pivot_wider(
#                                        names_from = Descripcion,
#                                        values_from = Ingresos
#                                      )  
                                   

###################################
# Tablas de las estacioanalidades #
###################################

#############
#  General  #
#############

# Pasado

Estacionalidad_sin_AC <-  ingresos_mensual  %>% dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
                                                                  dplyr::filter(Año!=Ano_actual)  %>%
                                                                  dplyr::group_by(Año,mes.cod,mes) %>%
                                                                  dplyr::summarise ("Ingresos"  = sum(`Ingresos`, na.rm = TRUE))



  
Estacionalidad_sin_AC <-   Estacionalidad_sin_AC  %>%
                                                        dplyr::group_by(Año) %>%                                                            
                                                        dplyr::mutate( 
                                                                        Ingreso_acumulado = cumsum(Ingresos), 
                                                                        Sumarecaudacion = sum(`Ingresos`),
                                                                        Estacionalidad = Ingresos/Sumarecaudacion,
                                                                        Estacionalidad_acumulada = cumsum(Estacionalidad),
                                                                        Fecha = paste(Año,mes,sep ="-"))  %>%
                                                        dplyr::arrange(Año,mes.cod)

 
# Actual

Ingresos_total_actual <- ingresos_anual  %>% 
                                         dplyr::filter(cod_fuentefinanciacion_3!=0)  %>%                                                                  
                                         dplyr::filter(Año==Ano_actual) %>% 
                                         dplyr::summarise ("Ingresos_total"  = sum(`Presupuesto actual`, na.rm = TRUE))  %>%
                                         dplyr:: mutate ( `Ingresos_total` = as.numeric (Ingresos_total) )

Ingresos_total_actual <- as.numeric(Ingresos_total_actual)


Estacionalidad_AC <-  ingresos_mensual  %>% 
                          dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
                          dplyr::filter(Año==Ano_actual)  %>%
                          dplyr::group_by(Año,mes.cod,mes) %>% 
                          dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE)) 


Estacionalidad_AC <-  Estacionalidad_AC %>% 
                      dplyr::group_by(Año) %>%                                                            
                      dplyr::mutate( 
                        Ingreso_acumulado = cumsum(Ingresos), 
                        Sumarecaudacion = Ingresos_total_actual,
                        Estacionalidad = Ingresos/Sumarecaudacion,
                        Estacionalidad_acumulada = cumsum(Estacionalidad),
                        Fecha = paste(Año,mes,sep ="-"))  %>%
                      dplyr::arrange(Año,mes.cod) 


Estacionalidad <-  dplyr::bind_rows(Estacionalidad_sin_AC,Estacionalidad_AC)

remove(Estacionalidad_sin_AC)
remove(Estacionalidad_AC)

Estacioanalidades_promedio <-  Estacionalidad %>% 
                                           dplyr::group_by(mes) %>%  
                                           dplyr::summarise('Estacionalidad promedio' =  mean(Estacionalidad, na.rm = TRUE),
                                                            'Estacionalidad acumulada promedio' = mean(Estacionalidad_acumulada, na.rm = TRUE))



Estacionalidad <- Estacionalidad %>%  dplyr::full_join(Estacioanalidades_promedio) 

Estacionalidad <- as.data.frame(Estacionalidad)

#   HC_Estacionalidad  <- highchart() %>% 
#     hc_title(text = "",
#              margin = 20, align = "center",
#              style = list(color = "#129", useHTML = TRUE)) %>% 
#     hc_subtitle(text = "",
#                 align = "right",
#                 style = list(color = "#634", fontWeight = "bold")) %>%
#     hc_credits(enabled = TRUE, # add credits
#                text = "" # href = "www.cgr.go.cr"
#     ) %>%
#     hc_legend(align = "left", verticalAlign = "top",
#               layout = "vertical", x = 0, y = 100) %>%
#     hc_exporting(enabled = TRUE) %>% 
#     hc_xAxis(categories = Estacionalidad$Fecha) %>% 
#     hc_add_series(name = "Estacionalidad", data = Estacionalidad$Estacionalidad) %>% 
#     hc_add_series(name = "Estacionalidad promedio", data = Estacionalidad$`Estacionalidad promedio`) %>% 
#     hc_chart(zoomType = "xy")
#   
#   HC_Estacionalidad
#   
#   
#   HC_Estacionalidad_acumulada  <- highchart() %>% 
#     hc_title(text = "",
#              margin = 20, align = "center",
#              style = list(color = "#129", useHTML = TRUE)) %>% 
#     hc_subtitle(text = "",
#                 align = "right",
#                 style = list(color = "#634", fontWeight = "bold")) %>%
#     hc_credits(enabled = TRUE, # add credits
#                text = "" # href = "www.cgr.go.cr"
#     ) %>%
#     hc_legend(align = "left", verticalAlign = "top",
#               layout = "vertical", x = 0, y = 100) %>%
#     hc_exporting(enabled = TRUE) %>% 
#     hc_xAxis(categories = Estacionalidad$Fecha) %>% 
#     hc_add_series(name = "Estacionalidad acumulada", data = Estacionalidad$`Estacionalidad_acumulada`) %>% 
#     hc_add_series(name = "Estacionalidad acumulada promedio", data = Estacionalidad$`Estacionalidad acumulada promedio`) %>% 
#     hc_chart(zoomType = "xy")
#     
#     
#   HC_Estacionalidad_acumulada   

# HC_Estacionalidad  <- highchart() %>% 
#   hc_title(text = "",
#            margin = 20, align = "center",
#            style = list(color = "#129", useHTML = TRUE)) %>% 
#   hc_subtitle(text = "",
#               align = "right",
#               style = list(color = "#634", fontWeight = "bold")) %>%
#   hc_credits(enabled = TRUE, # add credits
#              text = "" # href = "www.cgr.go.cr"
#   ) %>%
#   hc_legend(align = "left", verticalAlign = "top",
#             layout = "vertical", x = 0, y = 100) %>%
#   hc_tooltip(crosshairs = TRUE, backgroundColor = "#FCFFC5",
#              shared = TRUE, borderWidth = 5) %>% 
#   hc_exporting(enabled = TRUE) %>% 
#   hc_xAxis(categories = Estacionalidad$Fecha) %>% 
#   hc_add_series(name = "Estacionalidad", data = Estacionalidad$Estacionalidad) %>% 
#     hc_chart(zoomType = "xy")
#
# HC_Estacionalidad


###########################
#  Impuestos tributarios  #
###########################

# Ingresos_m  %>% dplyr::group_by(cod_subclase, subclase) %>% dplyr::summarise( 'total' = n())

# Pasado

IT_Estacionalidad_sin_AC <-  ingresos_mensual  %>% dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
  dplyr::filter(cod_subclase==11) %>% 
  dplyr::filter(Año!=Ano_actual)  %>%
  dplyr::group_by(Año,mes.cod,mes) %>%
  dplyr::summarise ("Ingresos"  = sum(`Ingresos`, na.rm = TRUE))



IT_Estacionalidad_sin_AC <-   IT_Estacionalidad_sin_AC  %>%
  dplyr::group_by(Año) %>%                                                            
  dplyr::mutate( 
    Ingreso_acumulado = cumsum(Ingresos), 
    Sumarecaudacion = sum(`Ingresos`),
    Estacionalidad = Ingresos/Sumarecaudacion,
    Estacionalidad_acumulada = cumsum(Estacionalidad),
    Fecha = paste(Año,mes,sep ="-"))  %>%
  dplyr::arrange(Año,mes.cod)

# Actual

IT_Ingresos_total_actual <- ingresos_anual  %>% 
  dplyr::filter(cod_fuentefinanciacion_3!=0)  %>%  
  dplyr::filter(cod_subclase==11) %>% 
  dplyr::filter(Año==Ano_actual) %>% 
  dplyr::summarise ("Ingresos_total"  = sum(`Presupuesto actual`, na.rm = TRUE))  %>%
  dplyr:: mutate ( `Ingresos_total` = as.numeric (Ingresos_total) )

IT_Ingresos_total_actual <- as.numeric(Ingresos_total_actual)


IT_Estacionalidad_AC <-  ingresos_mensual  %>% 
  dplyr::filter(cod_subclase==11) %>% 
  dplyr::filter(cod_fuentefinanciacion_3!=0)  %>% 
  dplyr::filter(Año==Ano_actual)  %>%
  dplyr::group_by(Año,mes.cod,mes) %>% 
  dplyr::summarise ("Ingresos"  = sum(Ingresos, na.rm = TRUE)) 


IT_Estacionalidad_AC <-  IT_Estacionalidad_AC %>% 
  dplyr::group_by(Año) %>%                                                            
  dplyr::mutate( 
    Ingreso_acumulado = cumsum(Ingresos), 
    Sumarecaudacion = Ingresos_total_actual,
    Estacionalidad = Ingresos/Sumarecaudacion,
    Estacionalidad_acumulada = cumsum(Estacionalidad),
    Fecha = paste(Año,mes,sep ="-"))  %>%
  dplyr::arrange(Año,mes.cod) 


IT_Estacionalidad <-  dplyr::bind_rows(IT_Estacionalidad_sin_AC,IT_Estacionalidad_AC)

remove(IT_Estacionalidad_sin_AC)
remove(IT_Estacionalidad_AC)

IT_Estacionalidad_promedio <-  IT_Estacionalidad %>% 
                         dplyr::group_by(mes) %>%  
                         dplyr::summarise('Estacionalidad promedio' =  mean(Estacionalidad, na.rm = TRUE),
                                          'Estacionalidad acumulada promedio' = mean(Estacionalidad_acumulada, na.rm = TRUE))



IT_Estacionalidad <- IT_Estacionalidad %>%  dplyr::full_join(IT_Estacionalidad_promedio) 

IT_Estacionalidad <- as.data.frame(IT_Estacionalidad)


######
## 5 # 
##################################################################################################### 
#####################################################################################################
#####################################################################################################
##                                              Exportación                                         #
#####################################################################################################
#####################################################################################################
##################################################################################################### 

# Directorio de exportación de las tablas #

setwd("C:/Users/regla.fiscal/Desktop/DashboardR/DR 000002 Ingresos/Scripts_tablas_dashboard")


# Archivo de datos

write.xlsx(ingresos_anual,"ingresos_anual.xlsx", overwrite = TRUE)
write.xlsx(ingresos_mensual,"ingresos_mensual.xlsx", overwrite = TRUE)
write.xlsx(ingresos_anual_s0,"ingresos_anual_s0.xlsx", overwrite = TRUE)


  
####### Indicadores ######

write.xlsx(indicador.1,"indicador.1.xlsx", overwrite = TRUE)
write.xlsx(indicador.2,"indicador.2.xlsx", overwrite = TRUE)
write.xlsx(indicador.3,"indicador.3.xlsx", overwrite = TRUE)
write.xlsx(indicador.4,"indicador.4.xlsx", overwrite = TRUE)
write.xlsx(indicador.5,"indicador.5.xlsx", overwrite = TRUE)
write.xlsx(indicador.6,"indicador.6.xlsx", overwrite = TRUE)


####### Impuestos  ######

write.xlsx(Impuestos, "Impuestos.xlsx", overwrite = TRUE)


######    Tablas: evolucioón del presupuesto anual   ######  

write.xlsx(tabla_1, "tabla_1.xlsx", overwrite = TRUE)

######   Tablas: evolucioón del ingreso mensual             ######  

write.xlsx(tabla_2, "tabla_2.xlsx", overwrite = TRUE)
write.xlsx(tabla_2_var, "tabla_2_var.xlsx", overwrite = TRUE)

#  Recaudación acumulada

write.xlsx(tabla.evo.mensual.1_acum, "tabla.evo.mensual.1_acum.xlsx", overwrite = TRUE)

#     Carga tributaria  

write.xlsx(tabla.evo.mensual.2_acum, "tabla.evo.mensual.2_acum.xlsx", overwrite = TRUE)


#  Ejecución  mensual 

write.xlsx(tabla.evo.mensual.3_acum, "tabla.evo.mensual.3_acum.xlsx", overwrite = TRUE)

######   Tablas:  Clasificador del ingreso   ####


##   # Clase
##   write.xlsx(tabla_clasi_c_1_1, "tabla_clasi_c_1_1.xlsx", overwrite = TRUE)
##   
##   # Subclase
##   write.xlsx(tabla_clasi_c_2_1, "tabla_clasi_c_2_1.xlsx", overwrite = TRUE)
##   
##   # Grupo
##   write.xlsx(tabla_clasi_c_3_1, "tabla_clasi_c_3_1.xlsx", overwrite = TRUE)
##   
##   # Subgrupo
##   write.xlsx(tabla_clasi_c_4_1, "tabla_clasi_c_4_1.xlsx", overwrite = TRUE)
##   
##   # Partida
##   write.xlsx(tabla_clasi_c_5_1, "tabla_clasi_c_5_1.xlsx", overwrite = TRUE)
##   
##   # Subpartida
##   write.xlsx(tabla_clasi_c_6_1, "tabla_clasi_c_6_1.xlsx", overwrite = TRUE)
##   
##   # Renglón
##   write.xlsx(tabla_clasi_c_7_1, "tabla_clasi_c_7_1.xlsx", overwrite = TRUE)
##   
##   # Subrenglón 
##   write.xlsx(tabla_clasi_c_8_1, "tabla_clasi_c_8_1.xlsx", overwrite = TRUE)
##   
##   # Fuente de Financiación
##   write.xlsx(tabla_clasi_c_9_1, "tabla_clasi_c_9_1.xlsx", overwrite = TRUE)

# Estacionalidades 

write.xlsx(Estacionalidad, "Estacionalidad.xlsx", overwrite = TRUE) 
write.xlsx(IT_Estacionalidad, "IT_Estacionalidad.xlsx", overwrite = TRUE) 



#################################################

end.time <- Sys.time()
time.taken <- end.time - start.time
time.taken
