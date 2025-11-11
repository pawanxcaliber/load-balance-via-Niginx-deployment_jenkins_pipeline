// Jenkins Pipeline definition for the DevSecOps project
pipeline {
    agent any

    // Ensure SNYK_TOKEN is configured in Jenkins Credentials
    environment {
        DOCKER_IMAGE_TAG = "v${BUILD_NUMBER}"
        BACKEND_IMAGE = "devsecops-project-backend"
        FRONTEND_IMAGE = "devsecops-project-frontend"
        // SNYK_TOKEN will be injected from Jenkins credentials
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

        // --- STAGE 2: MINIKUBE ENVIRONMENT SETUP ---
        stage('0: Setup Minikube Environment') {
            steps {
                script {
                    echo 'Setting up Docker environment for Minikube...'
                    sh 'eval $(minikube docker-env)'
                }
            }
        }
        
        // --- STAGE 3: SECURITY SCAN (SNYK) ---
        // CRITICAL FIX: Use the 'docker.image().inside()' syntax inside a script block 
        // to bypass the 'Invalid agent type' error.
        // --- STAGE 3: SECURITY SCAN (SNYK) ---
        stage('1: Snyk Vulnerability Scan') {
            steps {
                dir('backend') {
                    script {
                        // Launch the Snyk container to run the scan
                        docker.image('snyk/snyk').withRun('-v /var/run/docker.sock:/var/run/docker.sock') { container ->
                            echo 'Running Snyk Open Source dependency vulnerability scan inside snyk/snyk container...'
                            
                            // The 'snyk' command is available in the container's PATH.
                            sh "snyk auth \$SNYK_TOKEN"
                            
                            // Scan dependencies (Python requirements.txt) - set to fail on high severity
                            sh "snyk test --file=requirements.txt --severity-threshold=high"
                            
                            // Scan infrastructure (Dockerfile)
                            sh "snyk monitor --file=Dockerfile --docker"
                        } // end of withRun container block
                    } // end of script block
                } // end of dir block
            } // end of steps block
        }

        // --- STAGE 4: CODE QUALITY (Flake8) ---
        stage('2: Code Quality (Flake8 only)') {
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
                            cd /app && \\
                            pip install --no-cache-dir -r requirements.txt && \\
                            echo '✅ Running flake8 for lint check only...' && \\
                            flake8 || echo '⚠️ Flake8 warnings (non-blocking)'
                        "

                        echo "Cleaning up container..."
                        docker rm -f $CONTAINER_ID
                    '''
                }
            }
        }
        // --- STAGE 5: DOCKER BUILD & TAG (Minikube internal registry only) ---
        stage('3: Docker Build & Tag') {
            steps {
                script {
                    echo "Building images with tag: ${DOCKER_IMAGE_TAG}"
                    // Images are built directly into the Minikube internal registry (no push needed)
                    sh "docker build -t ${BACKEND_IMAGE}:${DOCKER_IMAGE_TAG} ./backend"
                    sh "docker build -t ${FRONTEND_IMAGE}:${DOCKER_IMAGE_TAG} ./frontend"
                }
            }
        }

        // --- STAGE 6: DEPLOY TO KUBERNETES ---
        stage('4: Deploy to Kubernetes') {
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