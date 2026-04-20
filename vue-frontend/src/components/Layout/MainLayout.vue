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

        <WhitelistPanel />
        <TaskDetailModal />
    </div>
</template>

<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import WhitelistPanel from '@/components/common/WhitelistPanel.vue'
import TaskDetailModal from '@/components/common/TaskDetailModel.vue'
</script>

<style lang="scss" scoped>
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
