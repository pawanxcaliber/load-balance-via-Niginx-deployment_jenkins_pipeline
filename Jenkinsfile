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

        // --- STAGE 2: MINIKUBE ENVIRONMENT SETUP & DEPENDENCIES ---
        stage('0: Setup Minikube Environment & Install Snyk') {
            steps {
                script {
                    echo 'Setting up Docker environment for Minikube...'
                    sh 'eval $(minikube docker-env)'
                    
                    echo 'Installing Snyk CLI using a dedicated root container...'
                    
                    // We run an Alpine container (small) as root, mount the Jenkins workspace
                    // and use npm/apk to install Snyk into the host's (Jenkins container's) PATH.
                    sh '''
                        # Install Node.js and Snyk CLI directly onto the Jenkins agent's filesystem 
                        # by mounting the /usr/local directory where binaries are stored.
                        docker run --rm \\
                            -v /usr/local:/mnt/local \\
                            node:18-alpine \\
                            /bin/sh -c "npm install -g snyk --prefix /mnt/local"
                    '''
                    
                    echo 'Snyk CLI installed and ready in /usr/local/bin.'
                }
            }
        }
        // --- STAGE 3: SECURITY SCAN (SNYK) ---
        stage('1: Snyk Vulnerability Scan') {
            steps {
                dir('backend') {
                    echo 'Running Snyk Open Source dependency vulnerability scan...'
                    
                    // --- FIX: Use the full path to the Snyk binary ---
                    def snykPath = "/usr/local/bin/snyk"
                    
                    // Authenticates the CLI using the injected environment variable
                    sh "${snykPath} auth \$SNYK_TOKEN"
                    
                    // Scan dependencies (Python requirements.txt) - set to fail on high severity
                    sh "${snykPath} test --file=requirements.txt --severity-threshold=high"
                    
                    // Scan infrastructure (Dockerfile)
                    sh "${snykPath} monitor --file=Dockerfile --docker"
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