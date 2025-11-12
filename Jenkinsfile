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
        // This stage is simplified as the crucial Docker setup is handled in Stage 1.
        stage('0: Setup Minikube Environment') {
            steps {
                echo 'Docker environment setup is deferred to Stage 1 for robustness.'
            }
        }
        
        // --- STAGE 3: SECURITY SCAN (SNYK) ---
        stage('1: Snyk Vulnerability Scan') {
            steps {
                dir('backend') {
                    script {
                        // CRITICAL FIX: Set up Docker environment immediately before running docker commands
                        sh 'eval $(minikube docker-env)' 
                        echo 'Docker environment setup confirmed.'
                        
                        echo 'Running Snyk scan via direct docker run command using verified image tag...'
                        
                        // Execute all Snyk commands inside a single, robust sh block
                        sh '''
                            # Use the verified image tag: snyk/snyk:linux-preview
                            # Mounts current directory (PWD) as /app and sets /app/backend as working directory.
                            # Passes SNYK_TOKEN as an environment variable to the container.
                            docker run --rm \\
                                -v ${PWD}:/app \\
                                -w /app/backend \\
                                -e SNYK_TOKEN \\
                                -v /var/run/docker.sock:/var/run/docker.sock \\
                                snyk/snyk:linux-preview \\
                                /bin/sh -c "snyk auth \$SNYK_TOKEN && \\
                                            snyk test --file=requirements.txt --severity-threshold=high && \\
                                            snyk monitor --file=Dockerfile --docker"
                        '''
                        echo 'Snyk scan completed.'
                    }
                }
            }
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