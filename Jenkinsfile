// Jenkins Pipeline definition for the DevSecOps project
pipeline {
    agent any

    environment {
        DOCKER_IMAGE_TAG = "v${BUILD_NUMBER}"
        BACKEND_IMAGE = "devsecops-project-backend"
        FRONTEND_IMAGE = "devsecops-project-frontend"
        SONAR_SCANNER = 'SonarQube_Server'
    }

    stages {

        // --- STAGE 1: CHECKOUT CODE ---
        stage('Checkout Code') {
            steps {
                echo 'Cloning repository into Jenkins workspace...'
                checkout scm
                sh 'echo "Workspace contents:" && ls -R'
            }
        }

        // --- STAGE 2: MINIKUBE ENVIRONMENT ---
        stage('0: Setup Minikube Environment') {
            steps {
                script {
                    echo 'Setting up Docker environment for Minikube...'
                    sh 'eval $(minikube docker-env)'
                }
            }
        }

        // --- STAGE 3: CODE QUALITY (Flake8 only) ---
        stage('1: Code Quality (Flake8 only)') {
            steps {
                dir('backend') {
                    sh '''
                        echo "Creating Python lint container..."
                        CONTAINER_ID=$(docker create -it python:3.10-slim tail -f /dev/null)

                        echo "Starting container..."
                        docker start $CONTAINER_ID

                        echo "Copying backend source code into container..."
                        docker cp . $CONTAINER_ID:/app

                        echo "Running flake8 linting inside container..."
                        docker exec $CONTAINER_ID /bin/bash -c "
                            cd /app && \
                            pip install --no-cache-dir -r requirements.txt && \
                            echo '✅ Running flake8 for lint check only...' && \
                            flake8 || echo '⚠️ Flake8 warnings (non-blocking)'
                        "

                        echo "Cleaning up container..."
                        docker rm -f $CONTAINER_ID
                    '''
                }
            }
        }

        // --- STAGE 4: SONARQUBE ANALYSIS ---
        stage('2: SonarQube Analysis') {
            steps {
                withSonarQubeEnv(SONAR_SCANNER) {
                    sh '''
                        cd backend && /usr/bin/sonar-scanner \
                            -Dsonar.projectKey=devsecops-backend \
                            -Dsonar.sources=. \
                            -Dsonar.host.url=${SONAR_HOST_URL} \
                            -Dsonar.login=${SONAR_AUTH_TOKEN} \
                            -Dsonar.python.file.suffixes=.py
                    '''
                }
            }
        }

        // --- STAGE 5: QUALITY GATE CHECK ---
        stage('3: SonarQube Quality Gate Check') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        // --- STAGE 6: DOCKER BUILD & TAG ---
        stage('4: Docker Build & Tag') {
            steps {
                script {
                    echo "Building images with tag: ${DOCKER_IMAGE_TAG}"
                    sh "docker build -t ${BACKEND_IMAGE}:${DOCKER_IMAGE_TAG} ./backend"
                    sh "docker build -t ${FRONTEND_IMAGE}:${DOCKER_IMAGE_TAG} ./frontend"
                }
            }
        }

        // --- STAGE 7: DEPLOY TO KUBERNETES ---
        stage('5: Deploy to Kubernetes') {
            steps {
                script {
                    echo 'Updating K8s manifests with new image tags...'
                    sh "sed -i 's|${BACKEND_IMAGE}:.*|${BACKEND_IMAGE}:${DOCKER_IMAGE_TAG}|g' K8's/02-backend-deployment.yaml"
                    sh "sed -i 's|${FRONTEND_IMAGE}:.*|${FRONTEND_IMAGE}:${DOCKER_IMAGE_TAG}|g' K8's/03-frontend-deployment.yaml"

                    echo 'Applying K8s manifests...'
                    sh 'kubectl apply -f K8\'s'

                    echo 'Waiting for deployment rollouts to complete...'
                    sh "kubectl rollout status deployment backend-deployment --timeout=5m"
                    sh "kubectl rollout status deployment frontend-deployment --timeout=5m"
                }
            }
        }
    }
}
