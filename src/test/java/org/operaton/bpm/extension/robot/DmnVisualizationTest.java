package org.operaton.bpm.extension.robot;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Integration test for DMN decision table visualization in Robot Framework log. */
class DmnVisualizationTest {

  @Test
  void dmnVisualizationKeywordRendersDecisionTable(@TempDir Path outputDir) throws Exception {
    String suitePath =
        Path.of("src", "test", "resources", "example", "DmnVisualization.robot")
            .toAbsolutePath()
            .toString();

    int exitCode = RobotCliTest.runRobot(outputDir.toString(), suitePath);
    assertThat(exitCode)
        .as("Robot Framework exit code (0 = all DMN visualization tests passed)")
        .isEqualTo(0);
  }
}
