const { HashTable } = require('./HashTable');

function testDefaultSize() {
	const hashTable = new HashTable();
	console.assert(hashTable.size !== undefined &&
								 hashTable.size !==null &&
								 hashTable.size > 0, 'testDefaultSize')
}

function testCanSetSize() {
	const size = 50;
	const hashTable = new HashTable(size);
	console.assert(hashTable.size===size, 'testCanSetSize')
}

function testSizeOfBuckets() {
	const size = 50;
	const hashTable = new HashTable(size);
	console.assert(hashTable.length===size, 'testSizeOfBuckets')
}

function testHashKeyIdempotent() {
	const hashTable = new HashTable();
	const key = 'foobar'
	hashedKey = hashTable.__hashFunction(key)
	console.assert(hashedKey===hashTable.__hashFunction(key), 'testHashKeyIdempotent')
	console.assert(hashedKey===hashTable.__hashFunction(key), 'testHashKeyIdempotent')
	console.assert(hashedKey===hashTable.__hashFunction(key), 'testHashKeyIdempotent')
	console.assert(hashedKey===hashTable.__hashFunction(key), 'testHashKeyIdempotent')
	console.assert(hashedKey===hashTable.__hashFunction(key), 'testHashKeyIdempotent')
}

function testHashKeyFitsSize() {
	const hashTable = new HashTable();
	const keys = ['foobar']
	keys.forEach(key => {
		console.assert(hashTable.__hashFunction(key) < hashTable.size, 'testHashKeyFitsSize')
	});
}

function testSetKeyValue() {
	const hashTable = new HashTable();
	const key = 'foo';
	const value = 'bar';
	const emptyBeforeSetValue = !hashTable.buckets
												 .find(bucket => bucket.length > 0);
	console.assert(emptyBeforeSetValue===true, 'testHashKeyFitsSize');

	hashTable.setValue(key, value);
	const notEmptyAfterSetValue = !!hashTable.buckets
									 .find(bucket => bucket.length > 0);
	console.assert(notEmptyAfterSetValue===true, 'testHashKeyFitsSize');
}

function testSetOneValue() {
	const hashTable = new HashTable();
	const key = 'foo';
	const value = 'bar';
	hashTable.setValue(key, value);
	const expected = hashTable.buckets
									 .filter(bucket => bucket.length > 0)
									 .length === 1;
	console.assert(expected===true, 'testHashKeyFitsSize');
}

function testGetValue() {
	const hashTable = new HashTable();
	const key = 'foo';
	const value = 'bar';
	hashTable.setValue(key, value);
	console.assert(hashTable.getValue(key)===value, 'testGetValue');
}

function testDeleteValue() {
	const hashTable = new HashTable();
	const key = 'foo';
	const value = 'bar';
	hashTable.setValue(key, value);
	const notEmptyAfterSetValue = !!hashTable.buckets
									 .find(bucket => bucket.length > 0);
	console.assert(notEmptyAfterSetValue===true, 'testDeleteValue');

	hashTable.deleteValue(key);
	const emptyAfterDeleteValue = !hashTable.buckets
												 .find(bucket => bucket.length > 0);
	console.assert(emptyAfterDeleteValue===true, 'testDeleteValue');
}

function testSeveralDifferentPairs() {
	const hashTable = new HashTable();
	const value = 'foobar';
	const pairs = [
		['welcome', value],
		['about', value],
		['contacts', value],
		['products', value],
		['services', value],
	]
	pairs.forEach(pair => hashTable.setValue(pair[0], pair[1]));
	console.log(hashTable.buckets);
}

testDefaultSize();
testCanSetSize();
testSizeOfBuckets();
testHashKeyIdempotent();
testHashKeyFitsSize();
testSetKeyValue();
testSetOneValue();
testGetValue();
testDeleteValue();
testSeveralDifferentPairs();
