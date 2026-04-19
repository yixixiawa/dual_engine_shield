<template>
    <div class="main-layout">
        <Sidebar />
        <main class="main-content">
            <router-view v-slot="{ Component }">
                <transition name="fade" mode="out-in">
                    <component :is="Component" />
                </transition>
            </router-view>
        </main>

        <!-- 后端服务器状态提示 -->
        <el-alert
            v-if="!isBackendOnline"
            :title="backendStatusMessage"
            type="error"
            show-icon
            :closable="false"
            class="backend-status-alert"
        />

        <WhitelistPanel />
        <TaskDetailModal />
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Sidebar from './Sidebar.vue'
import WhitelistPanel from '@/components/common/WhitelistPanel.vue'
import TaskDetailModal from '@/components/common/TaskDetailModel.vue'
import { getBackendStatus } from '@/utils/backendHealth'

const isBackendOnline = ref(true)
const backendStatusMessage = ref('')

// 检测后端服务器状态
const checkBackendStatus = async () => {
    const status = await getBackendStatus()
    isBackendOnline.value = status.isOnline
    backendStatusMessage.value = status.message
}

onMounted(() => {
    checkBackendStatus()
    // 每30秒检测一次后端状态
    setInterval(checkBackendStatus, 30000)
})
</script>

<style lang="scss" scoped>
.backend-status-alert {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
    max-width: 400px;
}


.main-layout {
    display: flex;
    min-height: 100vh;
}

.main-content {
    flex: 1;
    margin-left: 280px;
    padding: 2rem;
    transition: margin-left 0.3s ease;
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>