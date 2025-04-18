pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "bus-booking-app"
        CONTAINER_NAME = "bus-booking-app"
        APP_PORT = "5000"
    }

    stages {
        stage('Clone Repository') {
            steps {
                echo 'Cloning the repository...'
                git branch: 'main', url: 'https://github.com/Abhivedha-Anand/bus-booking.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'
                sh "docker build -t ${DOCKER_IMAGE} ."
            }
        }

        stage('Stop Previous Container') {
            steps {
                echo 'Stopping and removing previous container if exists...'
                sh """
                    docker stop ${CONTAINER_NAME} || true
                    docker rm ${CONTAINER_NAME} || true
                """
            }
        }

        stage('Run New Container') {
            steps {
                echo 'Running the new container...'
                sh "docker run -d -p ${APP_PORT}:${APP_PORT} --name ${CONTAINER_NAME} ${DOCKER_IMAGE}"
            }
        }
    }

    post {
        success {
            echo "App deployed successfully on port ${APP_PORT}!"
        }
        failure {
            echo "Build or deployment failed."
        }
    }
}
