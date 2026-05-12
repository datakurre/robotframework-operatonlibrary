package org.operaton.bpm.extension.robot;

import static org.assertj.core.api.Assertions.assertThat;

import org.graalvm.polyglot.Context;
import org.graalvm.polyglot.Source;
import org.graalvm.polyglot.Value;
import org.graalvm.python.embedding.GraalPyResources;
import org.junit.jupiter.api.Test;

/**
 * Diagnostic test: checks which Python {@code inspect} features required by <a
 * href="https://github.com/robotframework/PythonLibCore">PythonLibCore</a> are supported under
 * GraalPy.
 *
 * <p>PythonLibCore uses the following {@code inspect} APIs:
 *
 * <ul>
 *   <li>{@code inspect.getdoc(f)} — keyword documentation extraction
 *   <li>{@code inspect.unwrap(f)} — decorator-chain unwrapping
 *   <li>{@code inspect.getfullargspec(f)} — argument list / defaults / annotations
 *   <li>{@code inspect.ismethod(f)} — {@code self}-dropping logic (method vs function)
 *   <li>{@code inspect.getsourcelines(f)} — keyword source line numbers
 *   <li>{@code inspect.getfile(f)} — keyword source file path
 * </ul>
 *
 * <p>The last two ({@code getsourcelines}, {@code getfile}) are the highest-risk items because
 * Python source lives in GraalPy's VFS rather than on a real filesystem path. Failures are captured
 * as diagnostic strings rather than hard assertion failures so the full picture is visible in the
 * test output.
 */
class InspectCompatibilityTest {

  private static final String INSPECT_PROBE =
      """
      import inspect
      from functools import wraps
      results = {}

      # 1. getdoc
      def documented(): pass
      documented.__doc__ = "My doc."
      results['getdoc'] = inspect.getdoc(documented) == "My doc."

      # 2. unwrap
      def deco(f):
          @wraps(f)
          def w(*a, **k): return f(*a, **k)
          return w

      @deco
      def wrapped(x): pass
      results['unwrap'] = inspect.unwrap(wrapped).__name__ == 'wrapped'

      # 3. getfullargspec
      def sig(x: int, y: str = "hi") -> bool: pass
      spec = inspect.getfullargspec(sig)
      results['getfullargspec_args'] = spec.args == ['x', 'y']
      results['getfullargspec_defaults'] = spec.defaults == ('hi',)
      results['getfullargspec_annotations'] = spec.annotations.get('x') is int

      # 4. ismethod
      class C:
          def m(self): pass
      obj = C()
      results['ismethod_bound'] = inspect.ismethod(obj.m)
      results['ismethod_function'] = not inspect.ismethod(sig)

      # 5. getsourcelines (may fail in GraalPy VFS)
      try:
          lines, lineno = inspect.getsourcelines(documented)
          results['getsourcelines'] = True
      except Exception as e:
          results['getsourcelines'] = "FAIL: " + str(e)

      # 6. getfile (may fail in GraalPy VFS)
      try:
          f = inspect.getfile(documented)
          results['getfile'] = f
      except Exception as e:
          results['getfile'] = "FAIL: " + str(e)

      str(results)
      """;

  @Test
  void graalPySupportsInspectFeaturesRequiredByPythonLibCore() {
    String rawResults;
    try (Context context =
        GraalPyResources.contextBuilder()
            .allowAllAccess(true)
            .allowExperimentalOptions(true)
            .option("python.IsolateNativeModules", "true")
            .build()) {
      Source source = Source.newBuilder("python", INSPECT_PROBE, "<inspect-probe>").build();
      Value result = context.eval(source);
      rawResults = result.asString();
    } catch (Exception e) {
      throw new RuntimeException("GraalPy context evaluation failed", e);
    }

    System.out.println("[InspectCompatibilityTest] inspect probe results:\n  " + rawResults);

    // The core features needed for keyword argument/doc introspection must pass.
    assertThat(rawResults).contains("'getdoc': True");
    assertThat(rawResults).contains("'unwrap': True");
    assertThat(rawResults).contains("'getfullargspec_args': True");
    assertThat(rawResults).contains("'getfullargspec_defaults': True");
    assertThat(rawResults).contains("'getfullargspec_annotations': True");
    assertThat(rawResults).contains("'ismethod_bound': True");
    assertThat(rawResults).contains("'ismethod_function': True");

    // getsourcelines / getfile are VFS-path-dependent; log outcome but do not fail the build.
    boolean getsourcelinesOk = rawResults.contains("'getsourcelines': True");
    boolean getfileOk = rawResults.contains("'getfile': '") || rawResults.contains("'getfile': \"");
    System.out.println(
        "[InspectCompatibilityTest] getsourcelines supported: "
            + getsourcelinesOk
            + "  |  getfile supported: "
            + getfileOk);
  }
}
