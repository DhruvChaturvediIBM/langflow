// Run this in browser console to see the actual API response
fetch('http://localhost:3000/api/v1/all', {cache: 'no-store'})
  .then(r => r.json())
  .then(d => {
    // Find all DB2-related keys
    const allKeys = Object.keys(d);
    console.log('Total components:', allKeys.length);

    const db2Keys = allKeys.filter(k =>
      k.toLowerCase().includes('db2') ||
      k.includes('DB2') ||
      k.toLowerCase().includes('sql') && k.toLowerCase().includes('db')
    );

    console.log('\n=== DB2-related keys found ===');
    console.log(db2Keys);

    console.log('\n=== Full component details ===');
    db2Keys.forEach(key => {
      console.log(`\n--- ${key} ---`);
      const comp = d[key];
      console.log('Type:', typeof comp);
      console.log('Keys:', Object.keys(comp || {}));
      console.log('display_name:', comp?.display_name);
      console.log('description:', comp?.description);
      console.log('icon:', comp?.icon);
      console.log('Full object:', JSON.stringify(comp, null, 2).substring(0, 500));
    });
  });

// Made with Bob
