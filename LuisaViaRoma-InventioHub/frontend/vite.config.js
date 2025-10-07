import {fileURLToPath, URL} from 'node:url'

import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import { nodePolyfills } from 'vite-plugin-node-polyfills'
import Icons      from 'unplugin-icons/vite'
import Components from 'unplugin-vue-components/vite'
import IconsResolver from 'unplugin-icons/resolver'

export default defineConfig({
    plugins: [
        vue(),
        vueDevTools(),
        nodePolyfills(),
        Components({
            resolvers: [ IconsResolver({prefix:"Icon", alias:{fas: 'fa-solid'}}) ]
        }),
        Icons({autoInstall: true})

    ],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    server: {
        proxy: {
            '/api': {
                target: "http://localhost:8001/api",
                changeOrigin: true,
                rewrite: path => path.replace(/^\/api/, '')
            }
        }
    }

})


