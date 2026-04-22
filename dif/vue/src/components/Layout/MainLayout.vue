<template>
    <div class="main-layout">
        <Sidebar />
        <main class="main-content">
            <div class="main-content__inner">
                <router-view v-slot="{ Component }">
                    <transition name="fade" mode="out-in">
                        <component :is="Component" />
                    </transition>
                </router-view>
            </div>
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
@use '@/styles/variables.scss' as *;

.main-layout {
    display: grid;
    grid-template-columns: $sidebar-width minmax(0, 1fr);
    min-height: 100vh;
}

.main-content {
    min-width: 0;
    padding: $page-padding-y $page-padding-x;
}

.main-content__inner {
    min-width: 0;
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.24s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

@media (max-width: $breakpoint-md) {
    .main-layout {
        grid-template-columns: 1fr;
    }

    .main-content {
        padding-top: 1.25rem;
    }
}
</style>
