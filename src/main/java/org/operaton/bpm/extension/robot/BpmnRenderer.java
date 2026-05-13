package org.operaton.bpm.extension.robot;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Renders a BPMN diagram to SVG by invoking the bundled {@code bpmn-render.js} script via a {@code
 * node} subprocess.
 *
 * <p>The script is extracted from the classpath to a temporary file on first use and cached for the
 * lifetime of the JVM.
 *
 * <p>Requires Node.js 18+ on PATH at runtime. If {@code node} is not available, callers should
 * degrade gracefully (see {@link #isNodeAvailable()}).
 */
public class BpmnRenderer {

  private static final String SCRIPT_RESOURCE = "bpmn-render.js";

  private static volatile Path cachedScript;

  private BpmnRenderer() {}

  /**
   * Renders a BPMN diagram to SVG.
   *
   * @param jsonInput JSON string: {@code {"bpmn": "<xml>", "activities": [...]}}
   * @return SVG string
   * @throws Exception if node is not available, the script fails, or I/O errors occur
   */
  public static String renderSvg(String jsonInput) throws Exception {
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
          "bpmn-render failed (exit " + exitCode + ")" + (stderr.isEmpty() ? "" : ": " + stderr));
    }
    return new String(stdoutBytes, StandardCharsets.UTF_8);
  }

  /**
   * Returns {@code true} if {@code node} is executable on the current PATH.
   *
   * <p>The check is done by running {@code node --version}; result is not cached so that callers
   * can detect changes between calls (e.g., during testing).
   */
  public static boolean isNodeAvailable() {
    try {
      int exit =
          new ProcessBuilder("node", "--version").redirectErrorStream(true).start().waitFor();
      return exit == 0;
    } catch (Exception e) {
      return false;
    }
  }

  /**
   * Renders a DMN decision table to HTML using the bundled {@code dmn-render.js} script.
   *
   * <p>Self-contained: does not delegate to any other renderer class, so it compiles and runs
   * correctly even when {@code DmnRenderer} is not present on the classpath.
   *
   * @param jsonInput JSON string: {@code {"dmn": "<xml>", "decisionId": "...", "matchedRules":
   *     [...]}}
   * @return HTML string
   * @throws Exception if node is not available, the script fails, or I/O errors occur
   */
  public static String renderDmnHtml(String jsonInput) throws Exception {
    Path script = ensureDmnRenderScript();
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

  private static final String DMN_SCRIPT_RESOURCE = "dmn-render.js";
  private static volatile Path cachedDmnScript;

  private static Path ensureDmnRenderScript() throws IOException {
    if (cachedDmnScript != null && Files.exists(cachedDmnScript)) {
      return cachedDmnScript;
    }
    synchronized (BpmnRenderer.class) {
      if (cachedDmnScript != null && Files.exists(cachedDmnScript)) {
        return cachedDmnScript;
      }
      InputStream is = openResource(BpmnRenderer.class, DMN_SCRIPT_RESOURCE);
      if (is == null) {
        throw new IOException(
            DMN_SCRIPT_RESOURCE + " not found in classpath — rebuild with 'mvn package'");
      }
      try (is) {
        Path tmp = Files.createTempFile("dmn-render-", ".cjs");
        tmp.toFile().deleteOnExit();
        Files.write(tmp, is.readAllBytes());
        cachedDmnScript = tmp;
        return cachedDmnScript;
      }
    }
  }

  /**
   * Opens a classpath resource, trying multiple classloader strategies to handle fat-JAR and
   * GraalPy host-class contexts where {@link Class#getClassLoader()} may return {@code null}.
   */
  static InputStream openResource(Class<?> anchor, String name) {
    // 1. Class-relative (absolute path, equivalent to getClassLoader().getResourceAsStream(name))
    InputStream is = anchor.getResourceAsStream("/" + name);
    if (is != null) return is;
    // 2. Context classloader (may differ inside Truffle/GraalPy host method invocations)
    ClassLoader ctx = Thread.currentThread().getContextClassLoader();
    if (ctx != null) {
      is = ctx.getResourceAsStream(name);
      if (is != null) return is;
    }
    // 3. System classloader
    ClassLoader sys = ClassLoader.getSystemClassLoader();
    if (sys != null) {
      is = sys.getResourceAsStream(name);
    }
    return is;
  }

  private static Path ensureRenderScript() throws IOException {
    if (cachedScript != null && Files.exists(cachedScript)) {
      return cachedScript;
    }
    synchronized (BpmnRenderer.class) {
      if (cachedScript != null && Files.exists(cachedScript)) {
        return cachedScript;
      }
      InputStream is = openResource(BpmnRenderer.class, SCRIPT_RESOURCE);
      if (is == null) {
        throw new IOException(
            SCRIPT_RESOURCE + " not found in classpath — rebuild with 'mvn package'");
      }
      try (is) {
        Path tmp = Files.createTempFile("bpmn-render-", ".cjs");
        tmp.toFile().deleteOnExit();
        Files.write(tmp, is.readAllBytes());
        cachedScript = tmp;
        return cachedScript;
      }
    }
  }
}
