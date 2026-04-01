/**
 * 维度叠加组件
 * 在幽灵维度上显示半透明叠加层，提供额外信息和视觉效果
 */

import { useState, useEffect } from 'react';

export type Dimension = 'concepts' | 'emotion' | 'intent' | 'haunted-house';

export interface DimensionInfo {
  name: string;
  description: string;
  color: string;
  icon: string;
  opacity: number;
}

export const DIMENSIONS: Record<Dimension, DimensionInfo> = {
  concepts: {
    name: '概念维度',
    description: 'TypeScript核心概念的抽象空间',
    color: '#4299e1',
    icon: '🧠',
    opacity: 0.05
  },
  emotion: {
    name: '情绪维度',
    description: '学习过程中的情感状态映射',
    color: '#ed64a6',
    icon: '💓',
    opacity: 0.03
  },
  intent: {
    name: '意图维度',
    description: '代码背后的设计意图和模式',
    color: '#38b2ac',
    icon: '🎯',
    opacity: 0.04
  },
  'haunted-house': {
    name: '鬼屋维度',
    description: 'TypeScript高级特性的探索空间',
    color: '#9f7aea',
    icon: '🏚️',
    opacity: 0.06
  }
};

export interface DimensionOverlayProps {
  visible?: boolean;
  activeDimensions?: Dimension[];
  onDimensionToggle?: (dimension: Dimension, active: boolean) => void;
  intensity?: number; // 0-1
  interactive?: boolean;
}

export function DimensionOverlay({
  visible = true,
  activeDimensions = ['concepts', 'emotion'],
  onDimensionToggle,
  intensity = 0.5,
  interactive = true
}: DimensionOverlayProps) {
  const [dimensions, setDimensions] = useState<Dimension[]>(activeDimensions);
  const [showControls, setShowControls] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  // 从localStorage加载维度设置
  useEffect(() => {
    const saved = localStorage.getItem('ghost-dimension-overlay');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          setDimensions(parsed.filter((d): d is Dimension => d in DIMENSIONS));
        }
      } catch {
        // 忽略解析错误
      }
    }
  }, []);

  // 保存维度设置到localStorage
  useEffect(() => {
    localStorage.setItem('ghost-dimension-overlay', JSON.stringify(dimensions));
  }, [dimensions]);

  // 跟踪鼠标位置用于视觉效果
  useEffect(() => {
    if (!visible || !interactive) return;

    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [visible, interactive]);

  // 切换维度显示
  const toggleDimension = (dimension: Dimension) => {
    const newDimensions = dimensions.includes(dimension)
      ? dimensions.filter(d => d !== dimension)
      : [...dimensions, dimension];
    
    setDimensions(newDimensions);
    onDimensionToggle?.(dimension, !dimensions.includes(dimension));
  };

  // 计算叠加层样式
  const getOverlayStyle = (dimension: Dimension): React.CSSProperties => {
    const info = DIMENSIONS[dimension];
    
    // 计算基于鼠标位置的光晕效果
    const dx = mousePosition.x - window.innerWidth / 2;
    const dy = mousePosition.y - window.innerHeight / 2;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const maxDistance = Math.sqrt(
      Math.pow(window.innerWidth / 2, 2) + Math.pow(window.innerHeight / 2, 2)
    );
    
    const mouseIntensity = interactive ? (1 - distance / maxDistance) * 0.3 : 0;
    
    return {
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      pointerEvents: 'none',
      zIndex: 999,
      background: `radial-gradient(
        circle at ${mousePosition.x}px ${mousePosition.y}px,
        rgba(${hexToRgb(info.color)}, ${(info.opacity + mouseIntensity) * intensity}),
        transparent 70%
      )`,
      mixBlendMode: 'overlay',
      opacity: dimensions.includes(dimension) ? 1 : 0,
      transition: 'opacity 0.5s ease'
    };
  };

  // 辅助函数：十六进制颜色转RGB
  const hexToRgb = (hex: string): string => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result && result[1] && result[2] && result[3]
      ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
      : '66, 153, 225';
  };

  if (!visible) return null;

  return (
    <>
      {/* 维度叠加层 */}
      {Object.keys(DIMENSIONS).map((dimension) => (
        <div
          key={dimension}
          style={getOverlayStyle(dimension as Dimension)}
          className={`dimension-overlay dimension-${dimension}`}
        />
      ))}

      {/* 控制面板 */}
      {interactive && (
        <div
          style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            zIndex: 1000,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            borderRadius: '10px',
            padding: '10px',
            color: 'white',
            fontFamily: 'monospace',
            fontSize: '12px',
            cursor: 'pointer',
            border: '1px solid #666',
            transition: 'all 0.3s ease',
            maxWidth: showControls ? '300px' : '40px',
            overflow: 'hidden',
            height: showControls ? 'auto' : '40px'
          }}
          onClick={() => setShowControls(!showControls)}
          onMouseEnter={() => setShowControls(true)}
          onMouseLeave={() => setShowControls(false)}
        >
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: showControls ? 'flex-start' : 'center',
            gap: '10px'
          }}>
            <div style={{ fontSize: '20px' }}>🌌</div>
            {showControls && (
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
                  维度叠加控制器
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {(Object.entries(DIMENSIONS) as [Dimension, DimensionInfo][]).map(([dimension, info]) => (
                    <div
                      key={dimension}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '4px 8px',
                        backgroundColor: dimensions.includes(dimension)
                          ? `${info.color}33`
                          : 'transparent',
                        borderRadius: '4px',
                        border: `1px solid ${dimensions.includes(dimension) ? info.color : '#444'}`,
                        cursor: 'pointer'
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleDimension(dimension);
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={dimensions.includes(dimension)}
                        onChange={() => toggleDimension(dimension)}
                        onClick={(e) => e.stopPropagation()}
                        style={{ cursor: 'pointer' }}
                      />
                      <span style={{ color: info.color, marginRight: '4px' }}>
                        {info.icon}
                      </span>
                      <span style={{ flex: 1 }}>{info.name}</span>
                      <span style={{
                        fontSize: '10px',
                        color: '#aaa',
                        opacity: dimensions.includes(dimension) ? 1 : 0.5
                      }}>
                        {dimensions.includes(dimension) ? '显示中' : '已隐藏'}
                      </span>
                    </div>
                  ))}
                </div>
                <div style={{
                  marginTop: '10px',
                  fontSize: '10px',
                  color: '#888',
                  borderTop: '1px solid #444',
                  paddingTop: '8px'
                }}>
                  叠加强度: {(intensity * 100).toFixed(0)}%
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={intensity * 100}
                    onChange={(e) => {
                      // 强度调整可以通过上下文或回调处理
                      // 这里为了简化，只更新localStorage
                      localStorage.setItem('ghost-dimension-intensity', e.target.value);
                    }}
                    onClick={(e) => e.stopPropagation()}
                    style={{ width: '100%', marginTop: '4px' }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 维度指示器（角落显示） */}
      <div style={{
        position: 'fixed',
        top: '10px',
        right: '10px',
        zIndex: 998,
        display: 'flex',
        gap: '4px',
        opacity: 0.7
      }}>
        {dimensions.map(dimension => {
          const info = DIMENSIONS[dimension];
          return (
            <div
              key={dimension}
              style={{
                backgroundColor: `${info.color}33`,
                border: `1px solid ${info.color}`,
                borderRadius: '4px',
                padding: '2px 6px',
                fontSize: '10px',
                color: info.color,
                display: 'flex',
                alignItems: 'center',
                gap: '2px'
              }}
              title={`${info.name}: ${info.description}`}
            >
              <span>{info.icon}</span>
              <span style={{ opacity: 0.8 }}>{dimension === 'haunted-house' ? '鬼屋' : 
                dimension === 'concepts' ? '概念' : 
                dimension === 'emotion' ? '情绪' : '意图'}</span>
            </div>
          );
        })}
      </div>
    </>
  );
}

// 默认导出
export default DimensionOverlay;