import React from 'react';

const Filters = ({
  topics = [],
  selectedTopic,
  setSelectedTopic,
  keywords = [],
  selectedKeyword,
  setSelectedKeyword
}) => (
  <div style={{ display: 'flex', gap: '1.2rem', marginBottom: '1.5rem', alignItems: 'center' }}>
    <label>
      <b>Topic:</b>
      <select
        style={{ marginLeft: 8, padding: '0.4rem', borderRadius: 6 }}
        value={selectedTopic || ''}
        onChange={e => setSelectedTopic(e.target.value || null)}
      >
        <option value="">All</option>
        {topics.map(t => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>
    </label>
    {selectedTopic && (
      <label>
        <b>Keyword:</b>
        <select
          style={{ marginLeft: 8, padding: '0.4rem', borderRadius: 6 }}
          value={selectedKeyword || ''}
          onChange={e => setSelectedKeyword(e.target.value || null)}
        >
          <option value="">All</option>
          {keywords.map(k => (
            <option key={k} value={k}>{k}</option>
          ))}
        </select>
      </label>
    )}
  </div>
);

export default Filters;