@Library('ecdc-pipeline')
import ecdcpipeline.ContainerBuildNode
import ecdcpipeline.PipelineBuilder

project = "nexus-streamer-python"

container_build_nodes = [
  'centos7': ContainerBuildNode.getDefaultContainerBuildNode('centos7-gcc11')
]

// Define number of old builds to keep.
num_artifacts_to_keep = '1'

// Set number of old builds to keep.
properties([[
  $class: 'BuildDiscarderProperty',
  strategy: [
    $class: 'LogRotator',
    artifactDaysToKeepStr: '',
    artifactNumToKeepStr: num_artifacts_to_keep,
    daysToKeepStr: '',
    numToKeepStr: num_artifacts_to_keep
  ]
]]);

pipeline_builder = new PipelineBuilder(this, container_build_nodes)
pipeline_builder.activateEmailFailureNotifications()

builders = pipeline_builder.createBuilders { container ->
  pipeline_builder.stage("${container.key}: Checkout") {
    dir(pipeline_builder.project) {
      scm_vars = checkout scm
    }
    container.copyTo(pipeline_builder.project, pipeline_builder.project)
  }  // stage

  pipeline_builder.stage("${container.key}: Dependencies") {
    container.sh """
      which python
      python --version
      python -m pip install --user -r ${pipeline_builder.project}/requirements-dev.txt
    """
  } // stage

  pipeline_builder.stage("${container.key}: Formatting (black) ") {
    container.sh """
      which python
      python --version
      cd ${pipeline_builder.project}
      python -m black --check .
    """
  } // stage

  pipeline_builder.stage("${container.key}: Static Analysis (flake8) ") {
    container.sh """
      which python
      python --version
      cd ${pipeline_builder.project}
      python -m flake8
    """
  } // stage

  pipeline_builder.stage("${container.key}: Type Checking (mypy) ") {
    container.sh """
      which python
      python --version
      cd ${pipeline_builder.project}
      python -m mypy .
    """
  } // stage

  pipeline_builder.stage("${container.key}: Test") {
    def test_output = "TestResults.xml"
    container.sh """
      which python
      python --version
      cd ${pipeline_builder.project}
      python -m pytest --junitxml=${test_output}
    """
    container.copyFrom("${project}/${test_output}", ".")
    xunit thresholds: [failed(unstableThreshold: '0')], tools: [JUnit(deleteOutputFiles: true, pattern: '*.xml', skipNoTestFiles: false, stopProcessingIfError: true)]
  } // stage
}  // createBuilders

node {
  dir("${project}") {
    scm_vars = checkout scm
  }

  try {
    parallel builders
  } catch (e) {
    throw e
  }

  // Delete workspace when build is done
  cleanWs()
}
