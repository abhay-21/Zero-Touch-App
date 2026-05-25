// ================================================================
// Zero Touch App — Jenkinsfile
// ================================================================
// Pipeline: GitHub Push → Build Docker Image → Deploy on EC2
// Trigger:  GitHub Webhook on push to 'main'
// Server:   AWS EC2 t3.micro | Public IP: 40.192.3.142
// App Port: 5000 | Jenkins Port: 8080
// ================================================================

pipeline {

    agent any

    // ── Pipeline-wide variables ──────────────────────────────────
    environment {
        IMAGE_NAME     = 'zerotouch-app'
        CONTAINER_NAME = 'zerotouch-app'
        APP_PORT       = '5000'
        // Persistent volume path on EC2 host for SQLite DB
        DB_VOLUME_PATH = '/opt/zerotouch-data'
    }

    options {
        // Discard old builds — keep last 5 to save disk on t3.micro
        buildDiscarder(logRotator(numToKeepStr: '5'))
        // Kill the build if it takes longer than 15 minutes
        timeout(time: 15, unit: 'MINUTES')
        // Don't run concurrent builds (prevents port conflicts)
        disableConcurrentBuilds()
    }

    stages {

        // ── Stage 1: Checkout ────────────────────────────────────
        stage('📥 Checkout') {
            steps {
                echo '=== Pulling latest code from GitHub ==='
                checkout scm
                // Print commit info for audit trail
                sh 'git log -1 --format="%H %s %an" | tee build-info.txt'
                echo "Build triggered by commit: ${sh(script: 'git log -1 --format="%s"', returnStdout: true).trim()}"
            }
        }

        // ── Stage 2: Build Docker Image ──────────────────────────
        stage('🐳 Build Docker Image') {
            steps {
                echo '=== Building Docker image ==='
                sh """
                    docker build \
                        --tag ${IMAGE_NAME}:${BUILD_NUMBER} \
                        --tag ${IMAGE_NAME}:latest \
                        --label "build.number=${BUILD_NUMBER}" \
                        --label "build.git.commit=\$(git rev-parse --short HEAD)" \
                        --label "build.timestamp=\$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
                        .
                """
                echo "✅ Image built: ${IMAGE_NAME}:${BUILD_NUMBER}"
            }
        }

        // ── Stage 3: Stop Old Container (Zero-Downtime prep) ─────
        stage('🛑 Stop Old Container') {
            steps {
                echo '=== Stopping existing container (if any) ==='
                sh """
                    docker stop ${CONTAINER_NAME} 2>/dev/null || echo 'No running container to stop'
                    docker rm   ${CONTAINER_NAME} 2>/dev/null || echo 'No container to remove'
                """
            }
        }

        // ── Stage 4: Prepare Persistent Storage ──────────────────
        stage('📁 Prepare Data Volume') {
            steps {
                echo '=== Ensuring DB volume directory exists on host ==='
                sh "mkdir -p ${DB_VOLUME_PATH}"
            }
        }

        // ── Stage 5: Deploy New Container ────────────────────────
        stage('🚀 Deploy') {
            steps {
                echo '=== Starting new container ==='
                sh """
                    docker network create monitoring 2>/dev/null || true
                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        --restart unless-stopped \
                        --network monitoring \
                        -p ${APP_PORT}:5000 \
                        -v ${DB_VOLUME_PATH}:/app/instance \
                        -e FLASK_ENV=production \
                        -e DATABASE_URL=sqlite:////app/instance/zerotouch_social.db \
                        -e SECRET_KEY=zerotouch-bharat-prod-secret-2024 \
                        --memory="400m" \
                        --memory-swap="800m" \
                        --cpus="0.8" \
                        ${IMAGE_NAME}:latest
                """
                echo "✅ Container '${CONTAINER_NAME}' started on port ${APP_PORT}"
            }
        }

        // ── Stage 6: Health Check ─────────────────────────────────
        stage('🩺 Health Check') {
            steps {
                echo '=== Waiting for app to start... ==='
                sh 'sleep 10'
                sh """
                    curl --fail --silent --max-time 10 \
                         http://localhost:${APP_PORT}/health \
                    | python3 -m json.tool \
                    || (echo '❌ Health check FAILED' && exit 1)
                """
                echo "✅ App is live at http://40.192.3.142:${APP_PORT}"
            }
        }

        // ── Stage 7: Cleanup Old Images ──────────────────────────
        stage('🧹 Cleanup') {
            steps {
                echo '=== Removing dangling/old Docker images to free disk ==='
                sh 'docker image prune -f'
                // Keep only the last 3 tagged versions
                sh """
                    docker images ${IMAGE_NAME} --format "{{.Tag}}" \
                    | grep -E '^[0-9]+\$' \
                    | sort -n \
                    | head -n -3 \
                    | xargs -I {} docker rmi ${IMAGE_NAME}:{} 2>/dev/null || true
                """
            }
        }

    } // end stages

    // ── Post Actions ─────────────────────────────────────────────
    post {
        success {
            echo """
            ╔══════════════════════════════════════════╗
            ║  ✅ DEPLOYMENT SUCCESSFUL                 ║
            ║  App: http://40.192.3.142:5000           ║
            ║  Build: #${BUILD_NUMBER}                  ║
            ╚══════════════════════════════════════════╝
            """
        }
        failure {
            echo """
            ╔══════════════════════════════════════════╗
            ║  ❌ DEPLOYMENT FAILED — Build #${BUILD_NUMBER}  ║
            ║  Check Jenkins logs above for errors     ║
            ╚══════════════════════════════════════════╝
            """
            // Attempt to restart the previous container on failure
            sh "docker start ${CONTAINER_NAME} 2>/dev/null || echo 'Could not restart old container'"
        }
        always {
            echo '=== Printing running containers ==='
            sh 'docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"'
        }
    }

}
