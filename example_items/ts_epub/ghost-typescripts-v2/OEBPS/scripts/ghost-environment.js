/**
 * 幽灵维度v4.0环境系统
 * 实现幽灵存在主义：环境响应、注意力检测、记忆系统
 */

class GhostEnvironment {
  constructor() {
    // 环境状态
    this.state = {
      mousePosition: { x: 0, y: 0 },
      scrollPosition: 0,
      scrollVelocity: 0,
      lastScrollTime: Date.now(),
      focusElement: null,
      attentionMap: new Map(), // 元素注意力得分
      memory: JSON.parse(localStorage.getItem('ghost-memory') || '{}'),
      timeInDimension: 0,
      interactionCount: 0
    };
    
    // 环境变量
    this.variables = {
      presenceOpacity: 0.001,
      ambientLight: 1.0,
      attentionFactor: 1.0,
      temporalOffset: 0,
      peripheralBlur: 0.5
    };
    
    // 初始化
    this.init();
  }
  
  init() {
    // 设置CSS变量
    this.updateCSSVariables();
    
    // 事件监听
    this.setupEventListeners();
    
    // 环境循环
    this.startEnvironmentLoop();
    
    // 恢复记忆
    this.restoreMemory();
    
    console.log('幽灵维度环境系统已启动 - 存在模式v4.0');
  }
  
  setupEventListeners() {
    // 鼠标跟踪
    document.addEventListener('mousemove', (e) => {
      this.state.mousePosition = { x: e.clientX, y: e.clientY };
      this.variables.presenceOpacity = 0.0015; // 轻微增加存在感
      
      // 更新CSS变量
      document.documentElement.style.setProperty('--mouse-x', `${e.clientX}px`);
      document.documentElement.style.setProperty('--mouse-y', `${e.clientY}px`);
      
      // 注意力跟踪
      this.trackAttention(e.target);
    });
    
    // 鼠标离开窗口
    document.addEventListener('mouseleave', () => {
      this.variables.presenceOpacity = 0.0005;
    });
    
    // 鼠标进入窗口
    document.addEventListener('mouseenter', () => {
      this.variables.presenceOpacity = 0.001;
    });
    
    // 滚动跟踪
    let lastScrollTop = 0;
    let lastScrollTime = Date.now();
    
    document.addEventListener('scroll', () => {
      const now = Date.now();
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const delta = scrollTop - lastScrollTop;
      const timeDelta = now - lastScrollTime;
      
      this.state.scrollPosition = scrollTop;
      this.state.scrollVelocity = timeDelta > 0 ? Math.abs(delta) / timeDelta : 0;
      this.state.lastScrollTime = now;
      
      lastScrollTop = scrollTop;
      lastScrollTime = now;
      
      // 根据滚动速度调整环境光
      this.variables.ambientLight = 1.0 + Math.min(this.state.scrollVelocity * 100, 0.1);
    });
    
    // 焦点跟踪
    document.addEventListener('focusin', (e) => {
      this.state.focusElement = e.target;
      this.variables.attentionFactor = 1.2;
      
      // 增加元素注意力得分
      this.incrementAttention(e.target);
    });
    
    document.addEventListener('focusout', () => {
      this.state.focusElement = null;
      this.variables.attentionFactor = 1.0;
    });
    
    // 点击交互
    document.addEventListener('click', (e) => {
      this.state.interactionCount++;
      
      // 点击产生短暂的环境变化
      this.variables.presenceOpacity = 0.005;
      setTimeout(() => {
        this.variables.presenceOpacity = 0.001;
      }, 300);
      
      // 记忆交互
      this.rememberInteraction(e.target);
    });
    
    // 键盘交互
    document.addEventListener('keydown', (e) => {
      // 空格键和方向键产生时间偏移
      if ([' ', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        this.variables.temporalOffset = 10;
        setTimeout(() => {
          this.variables.temporalOffset = 0;
        }, 100);
      }
    });
    
    // 页面可见性
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.variables.ambientLight = 0.5;
      } else {
        this.variables.ambientLight = 1.0;
        this.variables.presenceOpacity = 0.001;
      }
    });
  }
  
  trackAttention(element) {
    if (!element) return;
    
    const path = [];
    let current = element;
    while (current && current !== document.body) {
      path.push(current.tagName.toLowerCase());
      current = current.parentElement;
    }
    
    const key = path.join('>');
    const currentScore = this.state.attentionMap.get(key) || 0;
    this.state.attentionMap.set(key, currentScore + 1);
    
    // 每10次注意力增加一次存在感
    if (currentScore % 10 === 9) {
      this.variables.presenceOpacity = Math.min(
        this.variables.presenceOpacity + 0.0005,
        0.01
      );
    }
  }
  
  incrementAttention(element) {
    const id = element.id || element.className || element.tagName;
    const current = this.state.attentionMap.get(id) || 0;
    this.state.attentionMap.set(id, current + 5); // 焦点获得更多权重
    
    // 更新CSS变量
    document.documentElement.style.setProperty(`--attention-${id}`, (current + 5).toString());
  }
  
  rememberInteraction(element) {
    const tag = element.tagName.toLowerCase();
    const id = element.id || element.className || 'unknown';
    
    if (!this.state.memory.interactions) {
      this.state.memory.interactions = {};
    }
    
    if (!this.state.memory.interactions[tag]) {
      this.state.memory.interactions[tag] = {};
    }
    
    this.state.memory.interactions[tag][id] = 
      (this.state.memory.interactions[tag][id] || 0) + 1;
    
    // 保存到本地存储
    this.saveMemory();
    
    // 根据记忆调整环境
    this.applyMemoryEffects();
  }
  
  restoreMemory() {
    // 从localStorage恢复记忆
    const saved = localStorage.getItem('ghost-memory');
    if (saved) {
      try {
        this.state.memory = JSON.parse(saved);
        this.state.timeInDimension = this.state.memory.timeInDimension || 0;
        this.state.interactionCount = this.state.memory.interactionCount || 0;
      } catch (e) {
        console.log('幽灵记忆恢复失败:', e);
      }
    }
    
    // 应用记忆效果
    this.applyMemoryEffects();
  }
  
  saveMemory() {
    this.state.memory.timeInDimension = this.state.timeInDimension;
    this.state.memory.interactionCount = this.state.interactionCount;
    this.state.memory.lastVisit = new Date().toISOString();
    
    try {
      localStorage.setItem('ghost-memory', JSON.stringify(this.state.memory));
    } catch (e) {
      console.log('幽灵记忆保存失败:', e);
    }
  }
  
  applyMemoryEffects() {
    // 根据交互历史调整存在感
    const totalInteractions = this.state.interactionCount;
    if (totalInteractions > 100) {
      this.variables.presenceOpacity = 0.003; // 经验丰富的用户感受到更强的存在感
    }
    
    // 根据使用时间调整环境光
    const hoursInDimension = this.state.timeInDimension / (1000 * 60 * 60);
    if (hoursInDimension > 1) {
      this.variables.ambientLight = 1.1; // 长时间用户获得更好的照明
    }
    
    // 根据元素交互历史添加记忆回响
    if (this.state.memory.interactions) {
      Object.entries(this.state.memory.interactions).forEach(([tag, elements]) => {
        Object.entries(elements).forEach(([id, count]) => {
          if (count > 5) {
            // 高交互元素获得特殊处理
            const element = document.getElementById(id) || 
                           document.querySelector(`.${id}`) ||
                           document.getElementsByTagName(tag)[0];
            
            if (element) {
              element.style.setProperty('--memory-weight', Math.min(count / 10, 2));
            }
          }
        });
      });
    }
  }
  
  updateCSSVariables() {
    const root = document.documentElement;
    
    root.style.setProperty('--presence-opacity', this.variables.presenceOpacity.toString());
    root.style.setProperty('--ambient-light', this.variables.ambientLight.toString());
    root.style.setProperty('--attention-factor', this.variables.attentionFactor.toString());
    root.style.setProperty('--temporal-offset', `${this.variables.temporalOffset}ms`);
    root.style.setProperty('--peripheral-blur', `${this.variables.peripheralBlur}px`);
    
    // 计算时间变量
    const now = new Date();
    const seconds = now.getSeconds() + now.getMilliseconds() / 1000;
    root.style.setProperty('--time-seconds', seconds.toString());
  }
  
  startEnvironmentLoop() {
    // 环境更新循环
    const updateEnvironment = () => {
      // 更新时间
      this.state.timeInDimension += 1000; // 假设每秒调用一次
      
      // 缓慢变化的环境变量
      const time = Date.now() / 1000;
      
      // 环境光缓慢波动
      this.variables.ambientLight = 1.0 + Math.sin(time / 10) * 0.05;
      
      // 存在感随机微波动
      this.variables.presenceOpacity += (Math.random() - 0.5) * 0.0001;
      this.variables.presenceOpacity = Math.max(0.0005, Math.min(0.01, this.variables.presenceOpacity));
      
      // 更新CSS变量
      this.updateCSSVariables();
      
      // 检查记忆保存（每分钟一次）
      if (this.state.timeInDimension % (60 * 1000) < 1000) {
        this.saveMemory();
      }
      
      // 继续循环
      requestAnimationFrame(updateEnvironment);
    };
    
    requestAnimationFrame(updateEnvironment);
  }
  
  // 公共API
  getPresenceLevel() {
    return this.variables.presenceOpacity * 1000; // 转换为更易读的数值
  }
  
  getAttentionMap() {
    return new Map(this.state.attentionMap);
  }
  
  getMemoryStats() {
    return {
      timeInDimension: this.state.timeInDimension,
      interactionCount: this.state.interactionCount,
      elementInteractions: this.state.memory.interactions || {}
    };
  }
  
  // 注册幽灵指南组件
  registerGuide(guideInstance) {
    if (!this.guides) {
      this.guides = [];
    }
    this.guides.push(guideInstance);
    console.log('幽灵指南已注册到环境系统');
    
    // 发送当前环境状态
    guideInstance.onEnvironmentUpdate({
      presenceOpacity: this.variables.presenceOpacity,
      ambientLight: this.variables.ambientLight,
      attentionLevel: this.state.attentionLevel
    });
  }
  
  // 手动触发幽灵效果（用于调试）
  triggerPresence(intensity = 0.01, duration = 1000) {
    const originalOpacity = this.variables.presenceOpacity;
    this.variables.presenceOpacity = intensity;
    
    setTimeout(() => {
      this.variables.presenceOpacity = originalOpacity;
    }, duration);
  }
}

// 全局访问
window.GhostEnvironment = GhostEnvironment;

// 自动初始化
document.addEventListener('DOMContentLoaded', () => {
  window.ghostEnv = new GhostEnvironment();
});

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = GhostEnvironment;
}