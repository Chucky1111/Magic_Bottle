/**
 * 情绪切换器组件
 * 允许用户在幽灵维度的不同情绪状态间切换
 */

import { useState, useEffect } from 'react';

export type Emotion = 'confused' | 'curious' | 'excited' | 'frustrated';

export interface EmotionTheme {
  color: string;
  backgroundColor: string;
  borderColor: string;
  icon: string;
}

export const EMOTION_THEMES: Record<Emotion, EmotionTheme> = {
  confused: {
    color: '#6b46c1',
    backgroundColor: '#faf5ff',
    borderColor: '#d6bcfa',
    icon: '🤔'
  },
  curious: {
    color: '#0987a0',
    backgroundColor: '#ebf8ff',
    borderColor: '#90cdf4',
    icon: '🔍'
  },
  excited: {
    color: '#c53030',
    backgroundColor: '#fff5f5',
    borderColor: '#fc8181',
    icon: '🎉'
  },
  frustrated: {
    color: '#744210',
    backgroundColor: '#fefcbf',
    borderColor: '#f6e05e',
    icon: '😤'
  }
};

export interface EmotionSwitcherProps {
  initialEmotion?: Emotion;
  onEmotionChange?: (emotion: Emotion) => void;
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  draggable?: boolean;
}

export function EmotionSwitcher({
  initialEmotion = 'curious',
  onEmotionChange,
  position = 'top-left',
  draggable = true
}: EmotionSwitcherProps) {
  const [currentEmotion, setCurrentEmotion] = useState<Emotion>(initialEmotion);
  const [isDragging, setIsDragging] = useState(false);
  const [positionStyle, setPositionStyle] = useState({ top: 20, left: 20 });
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  // 从localStorage加载保存的情绪
  useEffect(() => {
    const saved = localStorage.getItem('ghost-dimension-emotion');
    if (saved && saved in EMOTION_THEMES) {
      setCurrentEmotion(saved as Emotion);
      document.body.className = saved;
    } else {
      document.body.className = initialEmotion;
    }
  }, [initialEmotion]);

  // 保存情绪到localStorage并更新body类
  useEffect(() => {
    localStorage.setItem('ghost-dimension-emotion', currentEmotion);
    document.body.className = currentEmotion;
    onEmotionChange?.(currentEmotion);
  }, [currentEmotion, onEmotionChange]);

  // 应用情绪样式到文档根元素
  useEffect(() => {
    const theme = EMOTION_THEMES[currentEmotion];
    const root = document.documentElement;
    
    root.style.setProperty('--emotion-color', theme.color);
    root.style.setProperty('--emotion-bg', theme.backgroundColor);
    root.style.setProperty('--emotion-border', theme.borderColor);
  }, [currentEmotion]);

  // 处理情绪切换
  const handleEmotionChange = (emotion: Emotion) => {
    setCurrentEmotion(emotion);
    
    // 显示切换通知
    showNotification(`情绪切换为: ${emotion} ${EMOTION_THEMES[emotion].icon}`);
  };

  // 显示通知
  const showNotification = (message: string) => {
    // 移除现有的通知
    const existing = document.getElementById('emotion-notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.id = 'emotion-notification';
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 70px;
      right: 20px;
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 10px 15px;
      border-radius: 5px;
      z-index: 1001;
      font-family: sans-serif;
      font-size: 14px;
      animation: fadeInOut 2s ease-in-out;
      border-left: 4px solid ${EMOTION_THEMES[currentEmotion].color};
    `;

    // 添加动画样式
    const style = document.createElement('style');
    style.textContent = `
      @keyframes fadeInOut {
        0% { opacity: 0; transform: translateY(-10px); }
        10% { opacity: 1; transform: translateY(0); }
        90% { opacity: 1; transform: translateY(0); }
        100% { opacity: 0; transform: translateY(-10px); }
      }
    `;
    document.head.appendChild(style);

    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 2000);
    setTimeout(() => style.remove(), 2000);
  };

  // 拖动处理函数
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!draggable) return;
    
    setIsDragging(true);
    setDragOffset({
      x: e.clientX - positionStyle.left,
      y: e.clientY - positionStyle.top
    });
    
    e.preventDefault();
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      setPositionStyle({
        left: e.clientX - dragOffset.x,
        top: e.clientY - dragOffset.y
      });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragOffset]);

  // 根据props设置位置
  useEffect(() => {
    if (position === 'top-left') setPositionStyle({ top: 20, left: 20 });
    if (position === 'top-right') setPositionStyle({ top: 20, left: window.innerWidth - 180 });
    if (position === 'bottom-left') setPositionStyle({ top: window.innerHeight - 120, left: 20 });
    if (position === 'bottom-right') setPositionStyle({ top: window.innerHeight - 120, left: window.innerWidth - 180 });
  }, [position]);

  const currentTheme = EMOTION_THEMES[currentEmotion];

  return (
    <div
      className="emotion-switcher"
      style={{
        position: 'fixed',
        top: positionStyle.top,
        left: positionStyle.left,
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        border: `2px solid ${currentTheme.borderColor}`,
        borderRadius: '12px',
        padding: '12px',
        zIndex: 1000,
        cursor: draggable ? (isDragging ? 'grabbing' : 'grab') : 'default',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        minWidth: '160px',
        backdropFilter: 'blur(10px)',
        transition: 'all 0.3s ease',
        transform: isDragging ? 'scale(1.02)' : 'scale(1)'
      }}
      onMouseDown={handleMouseDown}
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '10px'
      }}>
        <div style={{
          fontWeight: 'bold',
          color: currentTheme.color,
          fontSize: '13px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          情绪维度
        </div>
        <div style={{
          fontSize: '18px',
          opacity: 0.8
        }}>
          {currentTheme.icon}
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '6px'
      }}>
        {(Object.entries(EMOTION_THEMES) as [Emotion, EmotionTheme][]).map(([emotion, theme]) => (
          <button
            key={emotion}
            onClick={() => handleEmotionChange(emotion)}
            style={{
              padding: '8px 6px',
              backgroundColor: emotion === currentEmotion ? theme.backgroundColor : '#f5f5f5',
              border: `2px solid ${emotion === currentEmotion ? theme.color : '#e0e0e0'}`,
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: emotion === currentEmotion ? 'bold' : 'normal',
              color: emotion === currentEmotion ? theme.color : '#666',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px'
            }}
            onMouseEnter={(e) => {
              if (emotion !== currentEmotion) {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
              }
            }}
            onMouseLeave={(e) => {
              if (emotion !== currentEmotion) {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }
            }}
          >
            <span>{theme.icon}</span>
            <span>{emotion === 'confused' ? '困惑' : 
                   emotion === 'curious' ? '好奇' : 
                   emotion === 'excited' ? '兴奋' : '挫败'}</span>
          </button>
        ))}
      </div>

      <div style={{
        marginTop: '10px',
        fontSize: '11px',
        color: '#888',
        textAlign: 'center',
        borderTop: '1px solid #eee',
        paddingTop: '8px'
      }}>
        当前: {currentEmotion === 'confused' ? '困惑' : 
              currentEmotion === 'curious' ? '好奇' : 
              currentEmotion === 'excited' ? '兴奋' : '挫败'}
      </div>
    </div>
  );
}

// 默认导出
export default EmotionSwitcher;