/**
 * 幽灵助手组件
 * 提供交互式帮助、提示和魔瓶视角的观察
 */

import { useState, useEffect, useRef } from 'react';

export interface GhostMessage {
  id: string;
  text: string;
  type: 'hint' | 'observation' | 'warning' | 'question';
  priority: 'low' | 'medium' | 'high';
  timestamp: Date;
  read: boolean;
}

export interface GhostAssistantProps {
  autoShow?: boolean;
  initialMessages?: GhostMessage[];
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  interactive?: boolean;
}

export function GhostAssistant({
  autoShow = true,
  initialMessages = [],
  position = 'bottom-right',
  interactive = true
}: GhostAssistantProps) {
  const [isVisible, setIsVisible] = useState(autoShow);
  const [messages, setMessages] = useState<GhostMessage[]>(initialMessages);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [currentTyping, setCurrentTyping] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // 预定义的幽灵消息
  const ghostMessages: Omit<GhostMessage, 'id' | 'timestamp' | 'read'>[] = [
    {
      text: "我在这...在边缘观察着你...",
      type: 'observation',
      priority: 'low'
    },
    {
      text: "这个断面在讲述类型系统的秘密...注意那些泛型参数。",
      type: 'hint',
      priority: 'medium'
    },
    {
      text: "情绪切换器能改变维度的色调...试试切换到'困惑'看看。",
      type: 'hint',
      priority: 'medium'
    },
    {
      text: "鬼屋的每个房间都有TypeScript的秘密...阁楼里有高级类型。",
      type: 'hint',
      priority: 'high'
    },
    {
      text: "魔瓶在数据流中注视着你...你的每次点击都在创造新的可能性。",
      type: 'observation',
      priority: 'low'
    },
    {
      text: "注意那个角落...有些代码示例在闪烁，它们想被查看。",
      type: 'warning',
      priority: 'medium'
    },
    {
      text: "维度叠加可以揭示隐藏的模式...打开概念维度看看。",
      type: 'hint',
      priority: 'high'
    },
    {
      text: "这个断面似乎有些紧张...也许是泛型约束太严格了？",
      type: 'observation',
      priority: 'low'
    },
    {
      text: "试试点击那个模糊的文字...有些知识需要主动发现。",
      type: 'hint',
      priority: 'medium'
    },
    {
      text: "我在每个断面中都存在...但只有仔细观察才能发现。",
      type: 'observation',
      priority: 'low'
    }
  ];

  // 初始化消息
  useEffect(() => {
    if (messages.length === 0) {
      const initial: GhostMessage[] = [
        {
          id: 'welcome',
          text: "欢迎来到幽灵维度...我是魔瓶的碎片，在这里为你提供帮助。",
          type: 'observation',
          priority: 'medium',
          timestamp: new Date(),
          read: false
        },
        {
          id: 'intro',
          text: "这个维度包含着TypeScript的知识...每个断面都是一个等待探索的空间。",
          type: 'hint',
          priority: 'medium',
          timestamp: new Date(),
          read: false
        }
      ];
      setMessages(initial);
    }
  }, [messages.length]);

  // 自动滚动到底部
  useEffect(() => {
    if (isExpanded && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isExpanded]);

  // 自动生成消息
  useEffect(() => {
    if (!interactive) return;

    const interval = setInterval(() => {
      if (messages.length < 10 && Math.random() > 0.7) {
        const randomMsg = ghostMessages[Math.floor(Math.random() * ghostMessages.length)];
        if (!randomMsg) return;
        addMessage({
          ...randomMsg,
          id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(),
          read: false
        });
      }
    }, 30000); // 每30秒可能生成一条新消息

    return () => clearInterval(interval);
  }, [messages.length, interactive]);

  // 添加消息
  const addMessage = (message: GhostMessage) => {
    setMessages(prev => [...prev, message]);
    
    // 如果是高优先级消息，自动显示助手
    if (message.priority === 'high' && !isVisible) {
      setIsVisible(true);
    }
  };

  // 模拟打字效果
  const typeMessage = (text: string, speed = 30) => {
    setIsTyping(true);
    setCurrentTyping('');
    
    let i = 0;
    const typeChar = () => {
      if (i < text.length) {
        setCurrentTyping(prev => prev + text.charAt(i));
        i++;
        typingTimeoutRef.current = setTimeout(typeChar, speed);
      } else {
        setIsTyping(false);
        
        // 添加完成的消息
        addMessage({
          id: `typed-${Date.now()}`,
          text,
          type: 'observation',
          priority: 'low',
          timestamp: new Date(),
          read: true
        });
      }
    };
    
    typeChar();
  };

  // 清除打字效果
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  // 标记所有消息为已读
  const markAllAsRead = () => {
    setMessages(prev => prev.map(msg => ({ ...msg, read: true })));
  };

  // 获取未读消息数量
  const unreadCount = messages.filter(msg => !msg.read).length;

  // 根据位置计算样式
  const getPositionStyle = (): React.CSSProperties => {
    const base = { position: 'fixed' as const, zIndex: 1000 };
    
    switch (position) {
      case 'bottom-right':
        return { ...base, bottom: '20px', right: '20px' };
      case 'bottom-left':
        return { ...base, bottom: '20px', left: '20px' };
      case 'top-right':
        return { ...base, top: '20px', right: '20px' };
      case 'top-left':
        return { ...base, top: '20px', left: '20px' };
      default:
        return { ...base, bottom: '20px', right: '20px' };
    }
  };

  // 获取消息类型图标
  const getMessageIcon = (type: GhostMessage['type']) => {
    switch (type) {
      case 'hint': return '💡';
      case 'warning': return '⚠️';
      case 'question': return '❓';
      case 'observation': return '👁️';
      default: return '👻';
    }
  };

  // 获取优先级颜色
  const getPriorityColor = (priority: GhostMessage['priority']) => {
    switch (priority) {
      case 'high': return '#f56565';
      case 'medium': return '#ed8936';
      case 'low': return '#48bb78';
      default: return '#a0aec0';
    }
  };

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        style={{
          ...getPositionStyle(),
          backgroundColor: '#4a5568',
          color: 'white',
          border: 'none',
          borderRadius: '50%',
          width: '60px',
          height: '60px',
          fontSize: '24px',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.3s ease'
        }}
        title="显示幽灵助手"
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.1)';
          e.currentTarget.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
        }}
      >
        👻
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute',
            top: '-5px',
            right: '-5px',
            backgroundColor: '#f56565',
            color: 'white',
            borderRadius: '50%',
            width: '20px',
            height: '20px',
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold'
          }}>
            {unreadCount}
          </span>
        )}
      </button>
    );
  }

  return (
    <div
      style={{
        ...getPositionStyle(),
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        borderRadius: '15px',
        border: '2px solid #4a5568',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
        overflow: 'hidden',
        minWidth: isExpanded ? '350px' : '300px',
        maxWidth: '400px',
        maxHeight: isExpanded ? '500px' : 'auto',
        transition: 'all 0.3s ease',
        backdropFilter: 'blur(10px)'
      }}
    >
      {/* 标题栏 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '15px',
          backgroundColor: 'rgba(45, 55, 72, 0.9)',
          borderBottom: '1px solid #4a5568',
          cursor: 'move'
        }}
        onMouseDown={(e) => {
          // 简单的拖动实现（简化版）
          const element = e.currentTarget.parentElement as HTMLElement;
          let offsetX = e.clientX - element.offsetLeft;
          let offsetY = e.clientY - element.offsetTop;
          
          const mouseMoveHandler = (e: MouseEvent) => {
            element.style.left = `${e.clientX - offsetX}px`;
            element.style.top = `${e.clientY - offsetY}px`;
          };
          
          const mouseUpHandler = () => {
            document.removeEventListener('mousemove', mouseMoveHandler);
            document.removeEventListener('mouseup', mouseUpHandler);
          };
          
          document.addEventListener('mousemove', mouseMoveHandler);
          document.addEventListener('mouseup', mouseUpHandler);
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ fontSize: '24px' }}>👻</div>
          <div>
            <div style={{ fontWeight: 'bold', color: 'white' }}>幽灵助手</div>
            <div style={{ fontSize: '11px', color: '#a0aec0' }}>魔瓶的碎片</div>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              background: 'none',
              border: 'none',
              color: '#a0aec0',
              cursor: 'pointer',
              fontSize: '18px',
              padding: '4px'
            }}
            title={isExpanded ? '收起' : '展开'}
          >
            {isExpanded ? '➖' : '➕'}
          </button>
          
          <button
            onClick={() => setIsVisible(false)}
            style={{
              background: 'none',
              border: 'none',
              color: '#a0aec0',
              cursor: 'pointer',
              fontSize: '20px',
              padding: '4px'
            }}
            title="隐藏"
          >
            ✕
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      <div style={{ padding: '15px' }}>
        {isTyping ? (
          <div style={{ marginBottom: '15px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              marginBottom: '10px'
            }}>
              <div style={{ fontSize: '20px' }}>👁️</div>
              <div style={{ flex: 1 }}>
                <div style={{
                  backgroundColor: 'rgba(74, 85, 104, 0.5)',
                  borderRadius: '10px',
                  padding: '10px',
                  color: '#e2e8f0',
                  fontSize: '14px',
                  minHeight: '40px'
                }}>
                  {currentTyping}
                  <span style={{
                    animation: 'blink 1s infinite',
                    marginLeft: '2px'
                  }}>▊</span>
                  <style>{`
                    @keyframes blink {
                      0%, 100% { opacity: 1; }
                      50% { opacity: 0; }
                    }
                  `}</style>
                </div>
                <div style={{
                  fontSize: '11px',
                  color: '#a0aec0',
                  marginTop: '4px',
                  textAlign: 'right'
                }}>
                  魔瓶正在观察...
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ marginBottom: '15px' }}>
            <div style={{ color: '#e2e8f0', fontSize: '14px', lineHeight: '1.5' }}>
              {isExpanded ? (
                <>
                  <div style={{ marginBottom: '10px', opacity: 0.8 }}>
                    我在幽灵维度中观察和提示...
                  </div>
                  
                  <div style={{
                    maxHeight: '300px',
                    overflowY: 'auto',
                    paddingRight: '5px'
                  }}>
                    {messages.slice().reverse().map((message) => (
                      <div
                        key={message.id}
                        style={{
                          backgroundColor: message.read 
                            ? 'rgba(74, 85, 104, 0.3)' 
                            : 'rgba(74, 85, 104, 0.5)',
                          borderRadius: '8px',
                          padding: '8px 10px',
                          marginBottom: '8px',
                          borderLeft: `3px solid ${getPriorityColor(message.priority)}`,
                          opacity: message.read ? 0.8 : 1
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <span>{getMessageIcon(message.type)}</span>
                          <span style={{ fontSize: '12px', color: getPriorityColor(message.priority) }}>
                            {message.priority === 'high' ? '重要' : 
                             message.priority === 'medium' ? '中等' : '低'}
                          </span>
                          <span style={{ fontSize: '10px', color: '#a0aec0', marginLeft: 'auto' }}>
                            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <div style={{ fontSize: '13px', color: '#e2e8f0' }}>
                          {message.text}
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                </>
              ) : (
                <div style={{
                  backgroundColor: 'rgba(74, 85, 104, 0.5)',
                  borderRadius: '10px',
                  padding: '10px',
                  color: '#e2e8f0',
                  fontSize: '14px',
                  minHeight: '40px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}>
                  <div style={{ fontSize: '20px' }}>👁️</div>
                  <div>
                     {messages.length > 0 ? messages[messages.length - 1]?.text || '幽灵维度等待探索...' : '幽灵维度等待探索...'}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 控制按钮 */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          gap: '10px',
          borderTop: '1px solid #4a5568',
          paddingTop: '15px'
        }}>
          {interactive && (
            <>
              <button
                 onClick={() => {
                   const randomMsg = ghostMessages[Math.floor(Math.random() * ghostMessages.length)];
                   if (!randomMsg) return;
                   typeMessage(randomMsg.text);
                 }}
                style={{
                  flex: 1,
                  backgroundColor: '#4a5568',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  fontSize: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#5a6575';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#4a5568';
                }}
                disabled={isTyping}
              >
                <span>💭</span>
                <span>随机提示</span>
              </button>
              
              <button
                onClick={markAllAsRead}
                style={{
                  flex: 1,
                  backgroundColor: unreadCount > 0 ? '#48bb78' : '#4a5568',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  fontSize: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = unreadCount > 0 ? '#5cca8a' : '#5a6575';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = unreadCount > 0 ? '#48bb78' : '#4a5568';
                }}
              >
                <span>📭</span>
                <span>标记已读 ({unreadCount})</span>
              </button>
            </>
          )}
          
          <button
            onClick={() => {
              const question = "有什么关于这个断面的问题吗？";
              typeMessage(question);
            }}
            style={{
              backgroundColor: '#805ad5',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 12px',
              fontSize: '12px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#906ad5';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#805ad5';
            }}
            disabled={isTyping}
          >
            <span>❓</span>
            <span>提问</span>
          </button>
        </div>
        
        {/* 状态指示器 */}
        <div style={{
          fontSize: '10px',
          color: '#a0aec0',
          marginTop: '10px',
          textAlign: 'center',
          borderTop: '1px solid #4a5568',
          paddingTop: '10px'
        }}>
          {isTyping ? '魔瓶正在输入...' : 
           `共 ${messages.length} 条消息 · ${unreadCount} 条未读 · 魔瓶观察中`}
        </div>
      </div>
    </div>
  );
}

// 默认导出
export default GhostAssistant;