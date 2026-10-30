// assets/charts.js — Mermaid 初始化
(function () {
  if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'neutral',
      securityLevel: 'loose',
      themeVariables: {
        primaryColor: '#fffdf9',
        primaryTextColor: '#292524',
        primaryBorderColor: '#8b6f47',
        lineColor: '#78716c',
        fontSize: '14px'
      }
    });
  }
})();
