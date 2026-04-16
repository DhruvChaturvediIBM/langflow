// Run this in browser console to see what's actually in the db2 key
fetch('http://localhost:3000/api/v1/all', {cache: 'no-store'})
  .then(r => r.json())
  .then(d => {
    console.log('=== Checking db2 key ===');
    const db2Data = d['db2'];
    console.log('Type:', typeof db2Data);
    console.log('Keys:', Object.keys(db2Data || {}));
    console.log('Full object:', JSON.stringify(db2Data, null, 2));

    console.log('\n=== Looking for SQL and Vector ===');
    const allKeys = Object.keys(d);
    const sqlKeys = allKeys.filter(k => k.includes('SQL') || k.includes('sql'));
    const vectorKeys = allKeys.filter(k => k.includes('Vector') || k.includes('vector'));
    console.log('SQL-related keys:', sqlKeys.filter(k => k.toLowerCase().includes('db2')));
    console.log('Vector-related keys:', vectorKeys.filter(k => k.toLowerCase().includes('db2')));
  });

// Made with Bob
