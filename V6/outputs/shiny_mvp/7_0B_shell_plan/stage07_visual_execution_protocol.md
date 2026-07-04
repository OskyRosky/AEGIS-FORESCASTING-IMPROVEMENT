# Stage 07 Visual Execution Protocol

From Stage 07 Block 7.0C forward, every block that changes `shiny_app/` must immediately launch the app and report visual execution details.

Mandatory protocol:

1. Start the Shiny app after every code change.
2. Provide local URL.
3. Provide port.
4. Provide HTTP status code.
5. Provide process ID when the app remains running.
6. Provide stdout and stderr log file paths.
7. Leave the app running when possible for Oscar to inspect.
8. Provide a PowerShell stop command: `Stop-Process -Id <PID> -Force`.
9. Do not proceed to the next Shiny-changing block until Oscar confirms visual inspection.
10. Record screenshots only if explicitly requested.
11. Do not recompute metrics.
12. Do not run models, forecasts, tournament, or champion logic.
13. Do not modify historical Stage 05, Stage 06, or Audit #6 artifacts.
14. Use V1 as the active project root.

For this 7.0B block, `shiny_app/` is not modified. The existing app is launched only as a visual baseline.
