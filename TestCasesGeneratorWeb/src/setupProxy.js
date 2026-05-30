const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
      pathRewrite: {
        '^/api': '', // 移除 /api 前缀，使请求直接打到 /ai_testcase_generator/...
      },
    })
  );
};
