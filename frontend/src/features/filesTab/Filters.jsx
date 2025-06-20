import React from 'react';

const Filters = ({ setFilter }) => (
  <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
    <button onClick={() => setFilter('all')}>All</button>
    <button onClick={() => setFilter('PDF')}>PDF</button>
    <button onClick={() => setFilter('IMAGE')}>Image</button>
    <button onClick={() => setFilter('TEXT')}>Text</button>
  </div>
);

export default Filters;