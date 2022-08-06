class HashTable {
	buckets = []
	size = 25

	constructor(size) {
		this.size = size || this.size;
		this.__createBuckets()
	}

	__hashFunction(key) {
		const chars = key.split('');
		let hash = 0;
		chars.forEach(c => {
			const code = c.charCodeAt(0);
			hash += code << 5;
		});
		return hash % this.size;
	}

	__createBuckets() {
		Array(this.size).fill([]).forEach(() => this.buckets.push([]));
	}

	get length() {
		return this.buckets.length;
	}

	setValue(key, value) {
		const hashedKey = this.__hashFunction(key);
		const index = this.buckets[hashedKey].findIndex((kv, index) => kv.has(key))
		if (index >= 0) {
			this.buckets[hashedKey][index] = new Set([key, value]);
		} else {
			this.buckets[hashedKey].push(new Set([key, value]));
		}
	}

	getValue(key) {
		const hashedKey = this.__hashFunction(key);
		const index = this.buckets[hashedKey].findIndex((kv, index) => kv.has(key))
		if (index >= 0) {
			return Array.from(this.buckets[hashedKey][index])[1];
		}
		return undefined;
	}

	deleteValue(key) {
		const hashedKey = this.__hashFunction(key);
		this.buckets[hashedKey] = this.buckets[hashedKey]
															.filter(kv => !kv.has(key));
	}

}
module.exports = {
	HashTable
}