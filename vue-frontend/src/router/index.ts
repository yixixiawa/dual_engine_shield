import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

// ✅ 改为懒加载模式，只匹配 Index.vue 文件
const allComponents = import.meta.glob('@/components/**/Index.vue', { eager: true })

// ✅ 更精确的路由生成逻辑
const generateRoutes = (): RouteRecordRaw[] => {
    const routeMap = new Map<string, RouteRecordRaw>()
    
    for (const [path, module] of Object.entries(allComponents)) {
        const match = path.match(/\/components\/(.+?)\/Index\.vue$/)
        if (!match) continue
        
        let routePath = match[1]
        // 去掉目录名中的 Detection 后缀
        routePath = routePath.replace(/Detection$/, '')
        routePath = '/' + routePath.toLowerCase()
        
        // 避免重复添加
        if (routeMap.has(routePath)) continue
        
        const routeName = routePath.slice(1).replace(/\//g, '-')
        
        // 从组件模块中提取 meta 数据
        const componentModule = module as any
        const meta = componentModule.default?.meta || {
            title: routePath.split('/').pop() || '页面',
            icon: 'Document',
            order: 999
        }
        
        routeMap.set(routePath, {
            path: routePath,
            name: routeName,
            component: () => import(/* @vite-ignore */ path), // 懒加载组件
            meta
        })
    }
    
    return Array.from(routeMap.values())
}

const autoRoutes = generateRoutes()

// 按优先级排序
autoRoutes.sort((a, b) => {
    const orderA = (a.meta as any)?.order ?? 999
    const orderB = (b.meta as any)?.order ?? 999
    return orderA - orderB
})

const routes: RouteRecordRaw[] = [
    {
        path: '/',
        redirect: '/combined'
    },
    ...autoRoutes,
    // ✅ 添加 404 路由
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/404.vue')
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router