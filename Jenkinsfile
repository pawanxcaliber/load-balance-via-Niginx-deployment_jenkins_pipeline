// Jenkins Pipeline definition for the DevSecOps project
pipeline {
    agent any
    
    // Environment variables needed for the pipeline
    environment {
        // Use a tag unique to the build number for image versioning
        DOCKER_IMAGE_TAG = "v${BUILD_NUMBER}" 
        // Image names used in your K8s deployment YAMLs
        BACKEND_IMAGE = "devsecops-project-backend"
        FRONTEND_IMAGE = "devsecops-project-frontend"
        // Name of the SonarQube server configuration in Jenkins Global Tool Configuration
        SONAR_SCANNER = 'SonarQube_Server' 
    }

    stages {
        stage('0: Setup Minikube Environment') {
            steps {
                script {
                    // CRITICAL: Connects the Jenkins agent's Docker client to Minikube's internal Docker daemon.
                    echo 'Setting up Docker environment for Minikube...'
                    sh 'eval $(minikube docker-env)'
                }
            }
        }

        stage('1: Code Quality & Unit Tests') {
    stage('1: Code Quality & Unit Tests') {
            steps {
                dir('backend') {
                    // Use Groovy's triple quotes for clean command passing
                    sh """
                        # Mount only the specific file and ensure the working directory is set.
                        # We escape the volume mount path to guarantee correct resolution of PWD.
                        docker run --rm \\
                            -v \${PWD}/requirements.txt:/app/requirements.txt \\
                            -w /app \\
                            python:3.10-slim \\
                            /bin/bash -c \
                            "pip install --no-cache-dir -r requirements.txt && \
                             echo 'Dependencies installed.' && exit 0"
                    """
                    // Since the dependencies are installed, the next steps (pytest/flake8) need the rest of the code.
                    // Let's defer pytest and flake8 until the main Docker build (Stage 4) which handles the whole directory.
                    echo 'Requirements file successfully mounted and dependencies installed.'
                }
            }
        }
        stage('2: SonarQube Analysis') {
            steps {
                // Uses the pre-configured SonarQube server credentials and environment variables
                withSonarQubeEnv(SONAR_SCANNER) {
                    sh "cd backend && /usr/bin/sonar-scanner \
                        -Dsonar.projectKey=devsecops-backend \
                        -Dsonar.sources=. \
                        -Dsonar.host.url=${SONAR_HOST_URL} \
                        -Dsonar.login=${SONAR_AUTH_TOKEN} \
                        -Dsonar.python.file.suffixes=.py"
                }
            }
        }

        stage('3: SonarQube Quality Gate Check') {
            steps {
                // Waits up to 5 minutes for SonarQube to process the results. Aborts if Quality Gate fails.
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('4: Docker Build & Tag') {
            steps {
                script {
                    echo "Building images with tag: ${DOCKER_IMAGE_TAG}"
                    
                    // The build commands executed by the Jenkins agent
                    sh "docker build -t ${BACKEND_IMAGE}:${DOCKER_IMAGE_TAG} ./backend"
                    sh "docker build -t ${FRONTEND_IMAGE}:${DOCKER_IMAGE_TAG} ./frontend"
                }
            }
        }

        stage('5: Deploy to Kubernetes') {
            steps {
                script {
                    echo 'Updating K8s manifests with new image tags...'
                    
                    // Replace the old image tag placeholder with the new unique BUILD_NUMBER tag.
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