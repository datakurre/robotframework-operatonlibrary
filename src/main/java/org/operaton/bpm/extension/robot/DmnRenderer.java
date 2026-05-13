package org.operaton.bpm.extension.robot;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Renders a DMN decision table to HTML by invoking the bundled {@code dmn-render.js} script via a
 * {@code node} subprocess.
 *
 * <p>The script is extracted from the classpath to a temporary file on first use and cached for the
 * lifetime of the JVM.
 *
 * <p>Requires Node.js 18+ on PATH at runtime. If {@code node} is not available, callers should
 * degrade gracefully (see {@link BpmnRenderer#isNodeAvailable()}).
 */
public class DmnRenderer {

  private static final String SCRIPT_RESOURCE = "dmn-render.js";

  private static volatile Path cachedScript;

  private DmnRenderer() {}

  /**
   * Renders a DMN decision table to HTML with matched-row highlighting.
   *
   * @param jsonInput JSON string: {@code {"dmn": "<xml>", "decisionId": "...", "matchedRules":
   *     [...]}}
   * @return HTML string
   * @throws Exception if node is not available, the script fails, or I/O errors occur
   */
  public static String renderHtml(String jsonInput) throws Exception {
    Path script = ensureRenderScript();
    ProcessBuilder pb = new ProcessBuilder("node", script.toString());
    pb.redirectErrorStream(false);

    Process proc = pb.start();
    try (OutputStream stdin = proc.getOutputStream()) {
      stdin.write(jsonInput.getBytes(StandardCharsets.UTF_8));
    }

    byte[] stdoutBytes = proc.getInputStream().readAllBytes();
    byte[] stderrBytes = proc.getErrorStream().readAllBytes();
    int exitCode = proc.waitFor();

    String stderr = new String(stderrBytes, StandardCharsets.UTF_8).strip();
    if (exitCode != 0) {
      throw new RuntimeException(
          "dmn-render failed (exit " + exitCode + ")" + (stderr.isEmpty() ? "" : ": " + stderr));
    }
    return new String(stdoutBytes, StandardCharsets.UTF_8);
  }

  private static Path ensureRenderScript() throws IOException {
    if (cachedScript != null && Files.exists(cachedScript)) {
      return cachedScript;
    }
    synchronized (DmnRenderer.class) {
      if (cachedScript != null && Files.exists(cachedScript)) {
        return cachedScript;
      }
      try (InputStream is =
          DmnRenderer.class.getClassLoader().getResourceAsStream(SCRIPT_RESOURCE)) {
        if (is == null) {
          throw new IOException(
              SCRIPT_RESOURCE + " not found in classpath — rebuild with 'mvn package'");
        }
        Path tmp = Files.createTempFile("dmn-render-", ".cjs");
        tmp.toFile().deleteOnExit();
        Files.write(tmp, is.readAllBytes());
        cachedScript = tmp;
        return tmp;
      }
    }
  }
}
