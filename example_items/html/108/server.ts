// 简单的静态文件服务器
const server = Bun.serve({
    port: 3000,
    async fetch(request) {
        const url = new URL(request.url);
        let path = url.pathname;
        
        // 默认页面
        if (path === '/') {
            path = '/index.html';
        }
        
        // 从public目录提供文件
        const filePath = `./public${path}`;
        const file = Bun.file(filePath);
        
        if (await file.exists()) {
            return new Response(file);
        }
        
        // 如果文件不存在，尝试提供根目录下的文件（如src）
        const rootFile = Bun.file(`.${path}`);
        if (await rootFile.exists()) {
            return new Response(rootFile);
        }
        
        return new Response('Not Found', { status: 404 });
    },
});

console.log(`服务器运行在 http://localhost:${server.port}`);
console.log(`游戏地址: http://localhost:${server.port}/index.html`);
console.log('按 Ctrl+C 停止服务器');