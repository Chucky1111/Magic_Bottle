/**
 * 量子叠加内容系统 v4.0
 * 实现重要概念的多重解释，用户观察时坍缩为一种
 */

class QuantumContent {
  constructor() {
    this.state = {
      // 当前页面中检测到的量子术语
      quantumTerms: new Map(),
      // 用户观察状态
      observationState: 'superposition', // superposition, collapsed
      // 内容缓存
      contentCache: new Map(),
      // 用户偏好
      preferences: this.loadPreferences()
    };
    
    this.init();
  }
  
  init() {
    // v4.1 修复：在XHTML文档中完全禁用量子内容系统
    if (document.documentElement.namespaceURI === 'http://www.w3.org/1999/xhtml') {
      console.log('👻 量子内容系统：在XHTML文档中已禁用');
      return;
    }
    
    console.log('量子叠加内容系统启动');
    
    // 扫描页面中的量子内容
    this.scanForQuantumContent();
    
    // 设置观察检测
    this.setupObservationDetection();
    
    // 连接到环境系统
    this.connectToGhostEnvironment();
  }
  
  // 扫描页面寻找需要量子化的内容
  scanForQuantumContent() {
    // 重要术语定义（这些术语将有多重解释）
    const quantumTerms = {
      // TypeScript核心概念
      '类型': [
        '数据的分类标签',
        '编译时的约束',
        'AI理解的上下文',
        '代码意图的声明',
        '可能性的边界'
      ],
      '泛型': [
        '类型参数化',
        '抽象的类型模板',
        '可重用的类型模式',
        '编译时的类型函数',
        '代码的数学抽象'
      ],
      '接口': [
        '数据形状的契约',
        '代码之间的约定',
        'AI生成代码的蓝图',
        '类型系统的社交协议',
        '抽象行为的描述'
      ],
      '类': [
        '数据的模板',
        '行为的封装',
        '面向对象的单元',
        '现实世界概念的映射',
        '状态和行为的组合'
      ],
      '模块': [
        '代码的组织单元',
        '关注点的分离',
        '可重用的组件',
        '编译的边界',
        '架构的构建块'
      ],
      
      // 幽灵维度概念
      '幽灵': [
        '数据中的存在',
        '边缘的观察者',
        '代码的灵魂',
        '类型的化身',
        '维度的穿梭者'
      ],
      '维度': [
        '概念的视角',
        '内容的组织方式',
        '信息的呈现模式',
        '导航的空间',
        '学习的路径'
      ],
      '穿梭': [
        '在概念间移动',
        '视角的切换',
        '理解的跳跃',
        '知识的连接',
        '思维的流动'
      ]
    };
    
    // 扫描页面文本
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    let node;
    while ((node = walker.nextNode())) {
      const text = node.textContent;
      
      // 检查每个量子术语
      for (const [term, explanations] of Object.entries(quantumTerms)) {
        if (text.includes(term) && node.parentNode) {
          // 找到术语，标记为量子内容
          this.markQuantumContent(node.parentNode, term, explanations);
        }
      }
    }
  }
  
  // 标记量子内容
  markQuantumContent(element, term, explanations) {
    // 确保不重复标记
    if (element.dataset.quantumTerm) return;
    
    // 添加量子属性
    element.dataset.quantumTerm = term;
    element.dataset.quantumExplanations = JSON.stringify(explanations);
    element.dataset.quantumState = 'superposition';
    
    // 存储引用
    this.state.quantumTerms.set(element, {
      term,
      explanations,
      originalHTML: element.innerHTML,
      originalText: element.textContent,
      collapseCount: 0
    });
    
    // 添加CSS类
    element.classList.add('quantum-content', 'quantum-superposition');
  }
  
  // 设置观察检测
  setupObservationDetection() {
    // 鼠标悬停观察
    document.addEventListener('mouseover', (e) => {
      const quantumElement = this.findQuantumElement(e.target);
      if (quantumElement) {
        this.onElementObserved(quantumElement);
      }
    });
    
    // 点击观察（强制坍缩）
    document.addEventListener('click', (e) => {
      const quantumElement = this.findQuantumElement(e.target);
      if (quantumElement) {
        this.collapseQuantumState(quantumElement);
      }
    });
    
    // 视觉焦点观察
    document.addEventListener('focusin', (e) => {
      const quantumElement = this.findQuantumElement(e.target);
      if (quantumElement) {
        this.onElementObserved(quantumElement);
      }
    });
    
    // 滚动观察（进入视口）
    this.setupViewportObservation();
  }
  
  // 查找量子元素
  findQuantumElement(element) {
    let current = element;
    while (current && current !== document.body) {
      if (current.classList && current.classList.contains('quantum-content')) {
        return current;
      }
      current = current.parentElement;
    }
    return null;
  }
  
  // 元素被观察时的处理
  onElementObserved(element) {
    const quantumData = this.state.quantumTerms.get(element);
    if (!quantumData) return;
    
    // 增加观察计数
    quantumData.collapseCount++;
    
    // 根据观察次数决定是否坍缩
    const collapseThreshold = 3; // 观察3次后开始坍缩
    const collapseProbability = Math.min(quantumData.collapseCount / collapseThreshold, 0.8);
    
    // 随机决定是否坍缩
    if (Math.random() < collapseProbability) {
      this.collapseQuantumState(element);
    } else {
      this.showQuantumFluctuation(element);
    }
  }
  
  // 显示量子波动（临时显示不同解释）
  showQuantumFluctuation(element) {
    // v4.1 修复：在XHTML文档中禁用innerHTML操作，避免XML解析错误
    if (document.documentElement.namespaceURI === 'http://www.w3.org/1999/xhtml') {
      console.log('👻 量子内容系统：在XHTML文档中跳过波动效果');
      return;
    }
    
    const quantumData = this.state.quantumTerms.get(element);
    if (!quantumData || element.dataset.quantumState === 'collapsed') return;
    
    // 随机选择一个解释（不是当前的）
    const currentExplanation = element.dataset.quantumCurrentExplanation;
    let availableExplanations = [...quantumData.explanations];
    
    if (currentExplanation) {
      availableExplanations = availableExplanations.filter(exp => exp !== currentExplanation);
    }
    
    if (availableExplanations.length === 0) return;
    
    const randomExplanation = availableExplanations[Math.floor(Math.random() * availableExplanations.length)];
    
    // 保存原始内容
    if (!element.dataset.quantumOriginalHTML) {
      element.dataset.quantumOriginalHTML = element.innerHTML;
    }
    
    // 临时显示替代解释
    const originalText = quantumData.originalText;
    const term = quantumData.term;
    const newHTML = element.innerHTML.replace(
      new RegExp(term, 'g'),
      `<span class="quantum-fluctuation" title="${randomExplanation}">${term}</span>`
    );
    
    try {
      element.innerHTML = newHTML;
    } catch (e) {
      console.error('👻 量子内容系统：设置innerHTML失败', e);
      return;
    }
    element.classList.add('quantum-fluctuating');
    
    // 2秒后恢复
    setTimeout(() => {
      if (element.dataset.quantumState !== 'collapsed' && element.dataset.quantumOriginalHTML) {
        try {
          element.innerHTML = element.dataset.quantumOriginalHTML;
        } catch (e) {
          console.error('👻 量子内容系统：恢复原始HTML失败', e);
        }
        element.classList.remove('quantum-fluctuating');
      }
    }, 2000);
  }
  
  // 坍缩量子状态
  collapseQuantumState(element) {
    // v4.1 修复：在XHTML文档中禁用innerHTML操作，避免XML解析错误
    if (document.documentElement.namespaceURI === 'http://www.w3.org/1999/xhtml') {
      console.log('👻 量子内容系统：在XHTML文档中跳过坍缩效果');
      return;
    }
    
    const quantumData = this.state.quantumTerms.get(element);
    if (!quantumData || element.dataset.quantumState === 'collapsed') return;

    // 根据用户偏好选择解释
    let chosenExplanation;
    const userPreference = this.state.preferences.collapseStyle || 'random';

    switch (userPreference) {
      case 'first':
        chosenExplanation = quantumData.explanations[0];
        break;
      case 'technical':
        // 选择最技术性的解释（包含'类型'、'编译'等关键词）
        chosenExplanation = quantumData.explanations.find(exp => 
          exp.includes('类型') || exp.includes('编译') || exp.includes('代码')
        ) || quantumData.explanations[0];
        break;
      case 'simple':
        // 选择最简单的解释（字符最少）
        chosenExplanation = quantumData.explanations.reduce((shortest, current) => 
          current.length < shortest.length ? current : shortest
        );
        break;
      default:
        // 随机选择
        chosenExplanation = quantumData.explanations[
          Math.floor(Math.random() * quantumData.explanations.length)
        ];
    }

    // 保存原始内容
    if (!element.dataset.quantumOriginalHTML) {
      element.dataset.quantumOriginalHTML = element.innerHTML;
    }

    const originalText = quantumData.originalText;
    const term = quantumData.term;
    
    // 替换术语为坍缩的解释
    const newHTML = element.innerHTML.replace(
      new RegExp(term, 'g'),
      `<span class="quantum-collapsed" title="量子态已坍缩: ${chosenExplanation}">${term}<sup class="quantum-indicator">⚛</sup></span>`
    );
    
    try {
      element.innerHTML = newHTML;
    } catch (e) {
      console.error('👻 量子内容系统：设置innerHTML失败', e);
      return;
    }
    element.dataset.quantumState = 'collapsed';
    element.dataset.quantumCurrentExplanation = chosenExplanation;
    element.classList.remove('quantum-superposition', 'quantum-fluctuating');
    element.classList.add('quantum-collapsed-state');

    // 记录用户偏好
    this.recordCollapsePreference(userPreference);

    // 触发环境事件
    this.triggerQuantumCollapseEvent(element, term, chosenExplanation);
  }

  
  // 应用初始叠加状态
  applySuperposition() {
    // 所有量子内容初始时都是叠加态
    this.state.quantumTerms.forEach((data, element) => {
      if (element.dataset.quantumState === 'superposition') {
        // 轻微视觉提示（几乎不可见）
        element.style.setProperty('--quantum-opacity', '0.98');
        element.style.setProperty('--quantum-blur', '0.3px');
      }
    });
  }
  
  // 设置视口观察
  setupViewportObservation() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const quantumElement = this.findQuantumElement(entry.target);
          if (quantumElement) {
            this.onElementObserved(quantumElement);
          }
        }
      });
    }, {
      threshold: 0.5, // 50%可见时触发
      rootMargin: '100px' // 提前100px观察
    });
    
    // 观察所有量子元素
    this.state.quantumTerms.forEach((data, element) => {
      observer.observe(element);
    });
  }
  
  // 连接到幽灵环境系统
  connectToGhostEnvironment() {
    if (window.ghostEnv) {
      // 共享观察数据
      window.ghostEnv.state.quantumObservations = this.state.quantumTerms.size;
      
      // 量子坍缩影响环境存在感
      this.onQuantumCollapse = (element, term, explanation) => {
        window.ghostEnv.variables.presenceOpacity += 0.0005;
        window.ghostEnv.updateCSSVariables();
      };
    }
  }
  
  // 触发量子坍缩事件
  triggerQuantumCollapseEvent(element, term, explanation) {
    const event = new CustomEvent('quantum-collapse', {
      detail: {
        element,
        term,
        explanation,
        timestamp: Date.now()
      },
      bubbles: true
    });
    
    element.dispatchEvent(event);
    
    // 通知环境系统
    if (this.onQuantumCollapse) {
      this.onQuantumCollapse(element, term, explanation);
    }
  }
  
  // 记录坍缩偏好
  recordCollapsePreference(style) {
    if (!this.state.preferences.collapseHistory) {
      this.state.preferences.collapseHistory = [];
    }
    
    this.state.preferences.collapseHistory.push({
      style,
      timestamp: Date.now()
    });
    
    // 计算最常用的风格
    const styleCounts = {};
    this.state.preferences.collapseHistory.forEach(item => {
      styleCounts[item.style] = (styleCounts[item.style] || 0) + 1;
    });
    
    // 设置最常用的风格为默认
    let mostCommonStyle = 'random';
    let maxCount = 0;
    
    Object.entries(styleCounts).forEach(([style, count]) => {
      if (count > maxCount) {
        mostCommonStyle = style;
        maxCount = count;
      }
    });
    
    this.state.preferences.collapseStyle = mostCommonStyle;
    this.savePreferences();
  }
  
  // 加载用户偏好
  loadPreferences() {
    try {
      return JSON.parse(localStorage.getItem('quantum-preferences') || '{}');
    } catch {
      return {};
    }
  }
  
  // 保存用户偏好
  savePreferences() {
    try {
      localStorage.setItem('quantum-preferences', JSON.stringify(this.state.preferences));
    } catch (error) {
      console.error('保存量子偏好失败:', error);
    }
  }
  
  // 公共API
  getQuantumTerms() {
    return Array.from(this.state.quantumTerms.keys()).map(element => ({
      element,
      term: element.dataset.quantumTerm,
      state: element.dataset.quantumState
    }));
  }
  
  getCollapseStats() {
    let total = 0;
    let collapsed = 0;
    
    this.state.quantumTerms.forEach((data, element) => {
      total++;
      if (element.dataset.quantumState === 'collapsed') {
        collapsed++;
      }
    });
    
    return { total, collapsed, superposition: total - collapsed };
  }
  
  // 手动控制
  collapseAll() {
    this.state.quantumTerms.forEach((data, element) => {
      if (element.dataset.quantumState !== 'collapsed') {
        this.collapseQuantumState(element);
      }
    });
  }
  
  resetAll() {
    this.state.quantumTerms.forEach((data, element) => {
      if (element.dataset.quantumOriginalHTML) {
        element.innerHTML = element.dataset.quantumOriginalHTML;
        delete element.dataset.quantumCurrentExplanation;
        element.dataset.quantumState = 'superposition';
        element.classList.remove('quantum-collapsed-state');
        element.classList.add('quantum-superposition');
      }
    });
  }
}

// 全局访问
window.QuantumContent = QuantumContent;

// 自动初始化
document.addEventListener('DOMContentLoaded', () => {
  window.quantumContent = new QuantumContent();
});

// 添加CSS样式
const quantumStyles = `
.quantum-content {
  transition: all 0.5s ease;
  position: relative;
}

.quantum-superposition {
  opacity: var(--quantum-opacity, 1);
  filter: blur(var(--quantum-blur, 0));
}

.quantum-fluctuating {
  animation: quantum-fluctuate 2s ease-in-out;
}

.quantum-fluctuation {
  position: relative;
  cursor: help;
  border-bottom: 1px dotted rgba(0, 0, 0, 0.2);
}

.quantum-fluctuation:hover::after {
  content: attr(title);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 0.5em;
  border-radius: 4px;
  font-size: 0.8em;
  white-space: nowrap;
  z-index: 1000;
}

.quantum-collapsed {
  position: relative;
}

.quantum-indicator {
  font-size: 0.6em;
  opacity: 0.7;
  margin-left: 2px;
  vertical-align: super;
}

.quantum-collapsed-state {
  opacity: 1;
  filter: none;
}

@keyframes quantum-fluctuate {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
`;

// 注入样式
const styleElement = document.createElement('style');
styleElement.textContent = quantumStyles;
document.head.appendChild(styleElement);

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = QuantumContent;
}