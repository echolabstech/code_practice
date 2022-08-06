toInt = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}

class Solution:
    def romanToInt(self, s: str) -> int:
        numChars = len(s)-1
        counter = 0
        output = 0
        while (counter <= numChars):
            left = toInt[s[counter]]

            if counter == numChars:
                output += left
                counter += 1
                continue

            right = toInt[s[counter+1]]
            if left < right:
                output += right - left
                counter += 2
                continue
            if left == right:
                output += left
                counter += 1
            if left > right:
                output += left
                counter += 1
        return output