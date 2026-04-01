/**
 * 幽灵指南 v4.0
 * 非显式导航系统，在边缘提供基于上下文的导航建议
 */

class GhostGuide {
  constructor() {
    this.state = {
      visible: false,
      currentPage: this.getCurrentPagePath(),
      guideOpacity: 0.001,
      memory: this.loadMemory()
    };
    
    this.guideElement = null;
    this.guideContent = null;
    
    this.init();
  }
  
  init() {
    // 注入样式
    this.injectStyles();
    
    // 创建指南元素
    this.createGuideElement();
    
    // 加载导航数据
    this.loadNavigationData();
    
    // 设置事件监听
    this.setupEventListeners();
    
    // 连接到幽灵环境
    this.connectToGhostEnvironment();
    
    console.log('幽灵指南启动，当前页面:', this.state.currentPage);
  }
  
  // 获取当前页面路径
  getCurrentPagePath() {
    const path = window.location.pathname;
    const hash = window.location.hash;
    return path.replace(/^.*\//, '') + hash;
  }
  
  // 注入CSS样式
  injectStyles() {
    const styles = `
.ghost-guide-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  opacity: var(--guide-opacity, 0.001);
  transition: opacity 0.8s ease, transform 0.5s ease;
  transform: translateY(0);
  pointer-events: none;
}

.ghost-guide-container.visible {
  opacity: 0.8;
  pointer-events: auto;
}

.ghost-guide-icon {
  width: 24px;
  height: 24px;
  background: var(--phantom-color, rgba(128, 128, 128, 0.1));
  border-radius: 50%;
  cursor: pointer;
  position: relative;
  transition: all 0.3s ease;
  box-shadow: 0 0 8px rgba(128, 128, 128, 0.2);
}

.ghost-guide-icon:hover {
  transform: scale(1.2);
  box-shadow: 0 0 12px rgba(128, 128, 128, 0.4);
}

.ghost-guide-icon::before,
.ghost-guide-icon::after {
  content: '';
  position: absolute;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 2px;
}

.ghost-guide-icon::before {
  width: 8px;
  height: 8px;
  top: 6px;
  left: 8px;
}

.ghost-guide-icon::after {
  width: 12px;
  height: 4px;
  bottom: 6px;
  left: 6px;
}

.ghost-guide-content {
  position: absolute;
  bottom: 40px;
  right: 0;
  width: 280px;
  background: rgba(20, 20, 30, 0.95);
  border: 1px solid rgba(128, 128, 128, 0.3);
  border-radius: 8px;
  padding: 16px;
  opacity: 0;
  transform: translateY(10px);
  transition: opacity 0.4s ease, transform 0.4s ease;
  pointer-events: none;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
}

.ghost-guide-content.visible {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}

.ghost-guide-title {
  font-size: 12px;
  color: rgba(200, 200, 220, 0.7);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.ghost-guide-links {
  list-style: none;
  margin: 0;
  padding: 0;
}

.ghost-guide-link {
  margin-bottom: 8px;
}

.ghost-guide-link a {
  color: rgba(220, 220, 240, 0.8);
  text-decoration: none;
  font-size: 14px;
  display: block;
  padding: 6px 10px;
  border-radius: 4px;
  transition: all 0.2s ease;
  border-left: 2px solid transparent;
}

.ghost-guide-link a:hover {
  background: rgba(100, 100, 140, 0.3);
  border-left: 2px solid rgba(160, 160, 220, 0.6);
  color: rgba(240, 240, 255, 0.95);
  padding-left: 14px;
}

.ghost-guide-link a:active {
  transform: scale(0.98);
}

.ghost-guide-context {
  font-size: 11px;
  color: rgba(180, 180, 200, 0.6);
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(128, 128, 128, 0.2);
  line-height: 1.4;
}
`;
    
    const styleEl = document.createElement('style');
    styleEl.textContent = styles;
    document.head.appendChild(styleEl);
  }
  
  // 创建指南元素
  createGuideElement() {
    const container = document.createElement('div');
    container.className = 'ghost-guide-container';
    container.id = 'ghost-guide';
    
    const icon = document.createElement('div');
    icon.className = 'ghost-guide-icon';
    icon.title = '幽灵指南';
    
    const content = document.createElement('div');
    content.className = 'ghost-guide-content';
    content.innerHTML = `
      <div class="ghost-guide-title">幽灵维度导航</div>
      <ul class="ghost-guide-links" id="ghost-guide-links">
        <!-- 动态填充 -->
      </ul>
      <div class="ghost-guide-context" id="ghost-guide-context">
        根据你的阅读历史和当前上下文建议
      </div>
    `;
    
    container.appendChild(icon);
    container.appendChild(content);
    document.body.appendChild(container);
    
    this.guideElement = container;
    this.guideContent = content;
    this.guideIcon = icon;
  }
  
  // 加载导航数据（简化版本）
  loadNavigationData() {
    // 主要章节映射
    const mainSections = [
      { title: '入口', path: 'entrance/index.xhtml' },
      { title: '概念目录', path: 'toc-concepts.xhtml' },
      { title: '情绪目录', path: 'toc-emotion.xhtml' },
      { title: '鬼屋目录', path: 'toc-haunted-house.xhtml' },
      { title: '意图目录', path: 'toc-intent.xhtml' },
      { title: '类型走廊', path: 'hallways/types/index.xhtml' },
      { title: '接口走廊', path: 'hallways/interfaces/index.xhtml' },
      { title: '泛型房间', path: 'rooms/generics/index.xhtml' },
      { title: '类房间', path: 'rooms/classes/index.xhtml' },
      { title: '模块房间', path: 'rooms/modules/index.xhtml' },
      { title: '秘密通道', path: 'secret-passages/configuration/index.xhtml' },
      { title: '附录', path: 'appendix.xhtml' }
    ];
    
    this.navigationData = mainSections;
    this.updateGuideLinks();
  }
  
  // 更新指南链接
  updateGuideLinks() {
    const linksContainer = document.getElementById('ghost-guide-links');
    if (!linksContainer) return;
    
    // 根据当前页面高亮相关链接
    const currentPage = this.state.currentPage;
    
    let linksHTML = '';
    this.navigationData.forEach(item => {
      const isCurrent = currentPage.includes(item.path) || currentPage === item.path;
      const className = isCurrent ? 'current' : '';
      linksHTML += `
        <li class="ghost-guide-link ${className}">
          <a href="${item.path}" data-path="${item.path}">${item.title}</a>
        </li>
      `;
    });
    
    linksContainer.innerHTML = linksHTML;
    
    // 添加点击事件
    linksContainer.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        this.navigateTo(link.getAttribute('href'));
      });
    });
  }
  
  // 导航到页面
  navigateTo(path) {
    console.log('幽灵指南导航到:', path);
    window.location.href = path;
  }
  
  // 设置事件监听
  setupEventListeners() {
    // 图标点击切换显示/隐藏
    this.guideIcon.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggleVisibility();
    });
    
    // 点击内容外部关闭
    document.addEventListener('click', (e) => {
      if (!this.guideElement.contains(e.target)) {
        this.hide();
      }
    });
    
    // 鼠标进入容器区域时增加可见性
    this.guideElement.addEventListener('mouseenter', () => {
      this.guideElement.style.opacity = '0.9';
    });
    
    this.guideElement.addEventListener('mouseleave', () => {
      if (!this.state.visible) {
        this.guideElement.style.opacity = 'var(--guide-opacity, 0.001)';
      }
    });
    
    // 响应幽灵环境变化
    window.addEventListener('ghost-environment-update', (e) => {
      this.onEnvironmentUpdate(e.detail);
    });
  }
  
  // 切换可见性
  toggleVisibility() {
    this.state.visible = !this.state.visible;
    this.guideElement.classList.toggle('visible', this.state.visible);
    this.guideContent.classList.toggle('visible', this.state.visible);
    
    // 更新环境变量
    document.documentElement.style.setProperty('--guide-opacity', this.state.visible ? '0.9' : '0.001');
  }
  
  // 显示指南
  show() {
    this.state.visible = true;
    this.guideElement.classList.add('visible');
    this.guideContent.classList.add('visible');
    document.documentElement.style.setProperty('--guide-opacity', '0.9');
  }
  
  // 隐藏指南
  hide() {
    this.state.visible = false;
    this.guideElement.classList.remove('visible');
    this.guideContent.classList.remove('visible');
    document.documentElement.style.setProperty('--guide-opacity', '0.001');
  }
  
  // 连接到幽灵环境
  connectToGhostEnvironment() {
    // 尝试连接到全局幽灵环境实例
    if (window.ghostEnv) {
      window.ghostEnv.registerGuide(this);
      console.log('幽灵指南已连接到幽灵环境');
    } else {
      // 等待环境加载
      setTimeout(() => this.connectToGhostEnvironment(), 500);
    }
  }
  
  // 环境更新回调
  onEnvironmentUpdate(envData) {
    // 根据环境数据调整指南行为
    const { presenceOpacity, ambientLight, attentionLevel } = envData;
    
    // 调整指南的不透明度基于环境存在感
    const guideOpacity = Math.max(0.001, presenceOpacity * 0.5);
    this.state.guideOpacity = guideOpacity;
    
    if (!this.state.visible) {
      this.guideElement.style.opacity = guideOpacity;
      document.documentElement.style.setProperty('--guide-opacity', guideOpacity);
    }
    
    // 根据注意力水平调整指南位置
    if (attentionLevel > 0.7) {
      this.guideElement.style.transform = 'translateY(-10px)';
    } else {
      this.guideElement.style.transform = 'translateY(0)';
    }
  }
  
  // 加载记忆
  loadMemory() {
    try {
      return JSON.parse(localStorage.getItem('ghost-guide-memory')) || {};
    } catch {
      return {};
    }
  }
  
  // 保存记忆
  saveMemory() {
    try {
      localStorage.setItem('ghost-guide-memory', JSON.stringify(this.state.memory));
    } catch (e) {
      console.warn('无法保存幽灵指南记忆:', e);
    }
  }
}

// 自动初始化
if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', () => {
    window.ghostGuide = new GhostGuide();
  });
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = GhostGuide;
}