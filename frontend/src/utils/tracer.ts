import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { SimpleSpanProcessor, ConsoleSpanExporter } from '@opentelemetry/sdk-trace-base';

// 初始化OpenTelemetry追踪器
const initTracer = () => {
  // 创建追踪器提供者
  const provider = new WebTracerProvider();

  // 配置控制台导出器（在浏览器环境中使用）
  const exporter = new ConsoleSpanExporter();

  // 添加处理器
  provider.addSpanProcessor(new SimpleSpanProcessor(exporter));

  // 注册提供者
  provider.register();

  console.log('OpenTelemetry tracer initialized');
};

// 获取追踪器
export const getTracer = () => {
  return (window as any).opentelemetry?.tracerProvider?.getTracer('ace-agent-frontend');
};

// 开始追踪
export const startSpan = (name: string, attributes?: Record<string, any>) => {
  const tracer = getTracer();
  if (!tracer) {
    console.warn('Tracer not initialized');
    return null;
  }

  const span = tracer.startSpan(name);
  if (attributes) {
    Object.entries(attributes).forEach(([key, value]) => {
      span.setAttribute(key, value);
    });
  }

  return span;
};

// 结束追踪
export const endSpan = (span: any) => {
  if (span) {
    span.end();
  }
};

export default initTracer;