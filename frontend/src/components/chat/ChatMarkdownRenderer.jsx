import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './ChatMarkdownRenderer.css';

const ChatMarkdownRenderer = ({ content }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeSanitize]}
      components={{
        p: ({ node, ...props }) => <p className="chat-md-paragraph" {...props} />,
        a: ({ node, ...props }) => (
          <a className="chat-md-link" {...props} target="_blank" rel="noopener noreferrer" />
        ),
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          return !inline && match ? (
            <SyntaxHighlighter style={oneDark} language={match[1]} PreTag="div" {...props}>
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code className="chat-md-inline-code" {...props}>
              {children}
            </code>
          );
        },
        blockquote: ({ node, ...props }) => <blockquote className="chat-md-blockquote" {...props} />,
        ul: ({ node, ...props }) => <ul className="chat-md-list" {...props} />,
        ol: ({ node, ...props }) => <ol className="chat-md-list" {...props} />,
        li: ({ node, ...props }) => <li className="chat-md-list-item" {...props} />,
        strong: ({ node, ...props }) => <strong className="chat-md-strong" {...props} />,
        em: ({ node, ...props }) => <em className="chat-md-em" {...props} />,
        hr: ({ node, ...props }) => <hr className="chat-md-hr" {...props} />,
        h1: ({ node, ...props }) => <h1 className="chat-md-heading" {...props} />,
        h2: ({ node, ...props }) => <h2 className="chat-md-heading" {...props} />,
        h3: ({ node, ...props }) => <h3 className="chat-md-heading" {...props} />,
        h4: ({ node, ...props }) => <h4 className="chat-md-heading" {...props} />,
        h5: ({ node, ...props }) => <h5 className="chat-md-heading" {...props} />,
        h6: ({ node, ...props }) => <h6 className="chat-md-heading" {...props} />,
        img: ({ node, ...props }) => <img className="chat-md-image" alt="" {...props} />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

export default ChatMarkdownRenderer;
