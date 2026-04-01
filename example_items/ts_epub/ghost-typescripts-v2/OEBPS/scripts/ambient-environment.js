// 幽灵环境引擎 v4.1
// 实现幽灵存在的极简：视觉简洁，环境复杂

class AmbientEnvironment {
  constructor() {
    // 环境状态变量
    this.state = {
      // 注意力热力图权重
      attentionWeights: {
        mouseFocus: 0.0,      // 鼠标焦点区域
        scrollPosition: 0.0,  // 滚动位置
        contentDensity: 0.0,  // 内容密度
        timeDecay: 0.0        // 时间衰减
      },
      
      // 情绪复合权重（同时性）
      emotionalComposite: {
        surprise: 0.0,    // 初生的惊喜
        chase: 0.0,       // 火焰追逐闪电
        disdain: 0.0,     // 轻蔑的嘲弄
        aftermath: 0.0    // 竞技场的散场时刻
      },
      
      // 环境参数（最终输出）
      ambientParams: {
        hueShift: 0,      // 色温偏移（度）
        saturation: 0.02, // 饱和度（%）
        lightness: 0.98,  // 亮度（%）
        opacity: 0.001,   // 存在感透明度
        blur: 0.5,        // 边缘模糊（px）
        drift: 0.0        // 时间漂移
      }
    };
    
    // 初始化
    this.init();
  }
  
  init() {
    // 绑定事件监听器
    this.bindEvents();
    
    // 初始环境分析
    this.analyzeContent();
    
    // 开始环境循环
    this.startEnvironmentLoop();
    
    console.log('👻 幽灵环境引擎启动 - 视觉极简，环境复杂');
  }
  
  bindEvents() {
    // 鼠标位置跟踪
    document.addEventListener('mousemove', (e) => {
      this.updateMouseFocus(e.clientX, e.clientY);
    });
    
    // 滚动跟踪
    let scrollTimeout;
    document.addEventListener('scroll', () => {
      this.updateScrollPosition();
      
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        this.state.attentionWeights.scrollPosition *= 0.5;
      }, 1000);
    });
    
    // 注意力焦点跟踪
    document.addEventListener('focusin', (e) => {
      if (e.target.matches('a, button, input, textarea, [tabindex]')) {
        this.state.attentionWeights.mouseFocus = 0.8;
      }
    });
    
    // 内容交互
    document.addEventListener('click', (e) => {
      // 轻微的环境扰动
      this.state.emotionalComposite.surprise = Math.min(0.3, this.state.emotionalComposite.surprise + 0.1);
      setTimeout(() => {
        this.state.emotionalComposite.surprise *= 0.3;
      }, 500);
    });
  }
  
  analyzeContent() {
    // 分析页面内容密度和复杂性
    const textElements = document.querySelectorAll('p, li, .phantom-note');
    let totalTextLength = 0;
    let complexSentenceCount = 0;
    
    textElements.forEach(el => {
      const text = el.textContent || '';
      totalTextLength += text.length;
      
      // 简单复杂性分析：长句、技术术语、中文混合
      const sentences = text.split(/[。！？.!?]/);
      sentences.forEach(sentence => {
        if (sentence.length > 50) complexSentenceCount++;
        if (sentence.includes('类型') || sentence.includes('接口') || sentence.includes('泛型')) {
          complexSentenceCount += 0.5;
        }
      });
    });
    
    // 设置内容密度权重
    const density = Math.min(1, totalTextLength / 5000);
    const complexity = Math.min(1, complexSentenceCount / 20);
    
    this.state.attentionWeights.contentDensity = density * 0.3 + complexity * 0.7;
    
    // 根据内容设置情绪基础值
    this.state.emotionalComposite.surprise = 0.1 + density * 0.2;  // 内容越多，惊喜潜力越大
    this.state.emotionalComposite.chase = complexity * 0.4;        // 复杂性驱动追逐感
    this.state.emotionalComposite.disdain = 0.05;                  // 基础轻蔑（对简单解释）
    this.state.emotionalComposite.aftermath = 0.0;                 // 初始无散场感
  }
  
  updateMouseFocus(x, y) {
    // 归一化坐标到0-1范围
    const normalizedX = x / window.innerWidth;
    const normalizedY = y / window.innerHeight;
    
    // 计算焦点强度（距离中心的距离）
    const centerX = 0.5;
    const centerY = 0.5;
    const distance = Math.sqrt(
      Math.pow(normalizedX - centerX, 2) + 
      Math.pow(normalizedY - centerY, 2)
    );
    
    // 焦点越偏离中心，注意力权重越高（幽灵在边缘）
    this.state.attentionWeights.mouseFocus = Math.min(0.9, distance * 1.5);
    
    // 更新CSS变量用于环境光照
    document.documentElement.style.setProperty('--mouse-x', `${normalizedX * 100}%`);
    document.documentElement.style.setProperty('--mouse-y', `${normalizedY * 100}%`);
  }
  
  updateScrollPosition() {
    const scrollPercent = window.scrollY / (document.body.scrollHeight - window.innerHeight);
    this.state.attentionWeights.scrollPosition = Math.min(0.7, scrollPercent * 0.8);
    
    // 滚动到底部时触发"散场时刻"
    if (scrollPercent > 0.95) {
      this.state.emotionalComposite.aftermath = Math.min(0.6, 0.5 + (scrollPercent - 0.95) * 2);
    } else {
      this.state.emotionalComposite.aftermath *= 0.9;
    }
  }
  
  calculateEnvironmentalParams() {
    // 计算总注意力权重
    const totalAttention = 
      this.state.attentionWeights.mouseFocus * 0.4 +
      this.state.attentionWeights.scrollPosition * 0.3 +
      this.state.attentionWeights.contentDensity * 0.2 +
      this.state.attentionWeights.timeDecay * 0.1;
    
    // 计算情绪复合值
    const emotionalTotal = 
      this.state.emotionalComposite.surprise * 0.4 +
      this.state.emotionalComposite.chase * 0.3 +
      this.state.emotionalComposite.disdain * 0.2 +
      this.state.emotionalComposite.aftermath * 0.1;
    
    // 设置环境参数
    
    // 1. 色温偏移：根据注意力和情绪的复杂函数
    const baseHue = 210; // 基础蓝色（好奇）
    const surpriseHue = 120; // 绿色（惊喜）
    const chaseHue = 30;   // 橙色（追逐）
    const disdainHue = 280; // 紫色（轻蔑）
    const aftermathHue = 0;  // 红色（散场）
    
    // v4.1 增强：增加色温变化幅度，使环境变化更明显
    this.state.ambientParams.hueShift = 
      baseHue * (1 - emotionalTotal * 0.5) +
      surpriseHue * this.state.emotionalComposite.surprise * 0.6 +
      chaseHue * this.state.emotionalComposite.chase * 0.8 +
      disdainHue * this.state.emotionalComposite.disdain * 0.4 +
      aftermathHue * this.state.emotionalComposite.aftermath * 0.2;
    
    // 2. 饱和度：极低，但有注意力依赖
    // v4.1 增强：增加饱和度变化幅度
    this.state.ambientParams.saturation = 0.05 + totalAttention * 0.1;
    
    // 3. 亮度：几乎不变，但有微妙变化
    // v4.1 增强：增加亮度变化幅度
    this.state.ambientParams.lightness = 0.95 - totalAttention * 0.05;
    
    // 4. 存在感透明度：幽灵的核心参数
    // v4.1 增强：增加透明度变化幅度
    this.state.ambientParams.opacity = 0.002 + emotionalTotal * 0.008;
    
    // 5. 边缘模糊：注意力越集中，边缘越清晰
    this.state.ambientParams.blur = 0.5 - totalAttention * 0.3;
    
    // 6. 时间漂移：缓慢的周期性变化
    const time = Date.now() / 1000;
    this.state.ambientParams.drift = Math.sin(time * 0.1) * 0.1;
  }
  
  updateCSSVariables() {
    const params = this.state.ambientParams;
    
    // 设置CSS自定义属性
    document.documentElement.style.setProperty(
      '--ambient-hue', 
      `${params.hueShift}deg`
    );
    document.documentElement.style.setProperty(
      '--ambient-saturation',
      `${params.saturation}%`
    );
    document.documentElement.style.setProperty(
      '--ambient-lightness',
      `${params.lightness}%`
    );
    document.documentElement.style.setProperty(
      '--presence-opacity',
      params.opacity.toString()
    );
    document.documentElement.style.setProperty(
      '--peripheral-blur',
      `${params.blur}px`
    );
    document.documentElement.style.setProperty(
      '--temporal-drift',
      params.drift.toString()
    );
    
    // 情绪权重变量（用于内容层）
    document.documentElement.style.setProperty(
      '--emotional-surprise',
      this.state.emotionalComposite.surprise.toString()
    );
    document.documentElement.style.setProperty(
      '--emotional-chase',
      this.state.emotionalComposite.chase.toString()
    );
    document.documentElement.style.setProperty(
      '--emotional-disdain',
      this.state.emotionalComposite.disdain.toString()
    );
    document.documentElement.style.setProperty(
      '--emotional-aftermath',
      this.state.emotionalComposite.aftermath.toString()
    );
  }
  
  startEnvironmentLoop() {
    let frameCount = 0;
    const updateEnvironment = () => {
      // 自动情绪波动（如果没有用户交互）
      const time = Date.now() / 1000;
      this.state.emotionalComposite.surprise = 0.1 + Math.sin(time * 0.3) * 0.05;
      this.state.emotionalComposite.chase = 0.05 + Math.sin(time * 0.5) * 0.03;
      this.state.emotionalComposite.disdain = 0.02 + Math.sin(time * 0.7) * 0.02;
      this.state.emotionalComposite.aftermath = 0.08 + Math.sin(time * 0.9) * 0.04;
      
      // 更新时间衰减
      this.state.attentionWeights.timeDecay = 
        (Math.sin(Date.now() / 30000) + 1) * 0.3; // 30秒周期，增强幅度
      
      // 计算新参数
      this.calculateEnvironmentalParams();
      
      // 更新CSS
      this.updateCSSVariables();
      
      // 每60帧（约1秒）输出一次调试信息
      frameCount++;
      if (frameCount % 60 === 0) {
        console.log('👻 环境引擎更新', {
          hue: this.state.ambientParams.hueShift.toFixed(1),
          saturation: this.state.ambientParams.saturation.toFixed(3),
          lightness: this.state.ambientParams.lightness.toFixed(3),
          opacity: this.state.ambientParams.opacity.toFixed(4),
          emotions: {
            surprise: this.state.emotionalComposite.surprise.toFixed(3),
            chase: this.state.emotionalComposite.chase.toFixed(3),
            disdain: this.state.emotionalComposite.disdain.toFixed(3),
            aftermath: this.state.emotionalComposite.aftermath.toFixed(3)
          }
        });
      }
      
      // 下一帧继续
      requestAnimationFrame(updateEnvironment);
    };
    
    // 启动循环
    requestAnimationFrame(updateEnvironment);
  }
}

// 自动初始化
document.addEventListener('DOMContentLoaded', () => {
  // 延迟启动，让页面先加载
  setTimeout(() => {
    window.ambientEnvironment = new AmbientEnvironment();
  }, 500);
});