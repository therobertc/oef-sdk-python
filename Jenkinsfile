pipeline {

    agent {
        docker {
            image "gcr.io/organic-storm-201412/oef-sdk-python-image:latest"
            }
        }

    stages {

        stage('Builds & Tests'){

            parallel{

                stage('Test') {
                    steps {
                        sh 'tox'
                    }
                }

                stage('Lint'){
                    steps{
                        sh 'tox -e flake8'
                    }
                }

                stage('Docs'){
                    steps{
                        sh 'tox -e docs'
                    }
                }

            }

        }

    }
}
