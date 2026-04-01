/**
 * 幽灵维度断面类型定义
 * v3版本：移除feeling块，增强魔瓶本质
 */

export type Emotion = 'confused' | 'curious' | 'excited' | 'frustrated';

export type Dimension = 'concepts' | 'emotion' | 'intent' | 'haunted-house';

export type SectionType = 
  | 'entrance'
  | 'basic-types'
  | 'interface-basics'
  | 'type-inference'
  | 'any-unknown'
  | 'arrays-tuples'
  | 'enums'
  | 'type-aliases'
  | 'optional-readonly'
  | 'extends-implements'
  | 'generic-basics'
  | 'generic-constraints'
  | 'utility-types'
  | 'conditional-types'
  | 'class-basics'
  | 'access-modifiers'
  | 'inheritance'
  | 'abstract-interfaces'
  | 'module-basics'
  | 'import-export'
  | 'namespace'
  | 'module-resolution'
  | 'tsconfig-basics'
  | 'compiler-options'
  | 'eslint-prettier'
  | 'ai-tools'
  | 'prompt-engineering'
  | 'ai-collaboration'
  | 'ghost-types'
  | 'error-index'
  | 'conclusion'
  | 'appendix';

export interface CodeExample {
  code: string;
  description?: string;
  highlights?: string[];
}

export interface AIConversation {
  human: string;
  ai: string;
  analysis?: string;
}

export interface Exercise {
  description: string;
  solution?: string;
  hints?: string[];
}

export interface PhantomNote {
  text: string;
  location?: 'margin' | 'inline' | 'footer';
}

export interface NavigationLink {
  text: string;
  href: string;
  dimension?: Dimension;
}

export interface Section {
  id: string;
  type: SectionType;
  title: string;
  path: string;
  
  // 魔瓶观察：不再是feeling块，而是直接的环境设定
  environment: {
    dominantEmotion: Emotion;
    visualDescription: string;
    atmosphere: string;
  };
  
  // 核心内容
  introduction?: string;
  phantomNotes?: PhantomNote[];
  codeExamples?: CodeExample[];
  aiConversations?: AIConversation[];
  exercises?: Exercise[];
  
  // 导航
  relatedSections?: NavigationLink[];
  nextSections?: NavigationLink[];
  
  // 元数据
  dimension: Dimension;
  keywords?: string[];
  createdAt: Date;
  updatedAt: Date;
}

/**
 * 断面生成器配置
 */
export interface SectionGeneratorConfig {
  includeFeelingBlocks: boolean; // v3中为false
  includeEmotionSwitcher: boolean; // v3中为true
  includeDimensionOverlay: boolean; // v3中为true
  includeGhostAssistant: boolean; // v3中为true
}

/**
 * 幽灵助手提示
 */
export interface GhostAssistantHint {
  id: string;
  text: string;
  context?: string;
  priority: 'low' | 'medium' | 'high';
}