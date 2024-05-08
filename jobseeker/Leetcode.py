from typing import List

def maximal_square(matrix:List[List[str]])-> int:
    area=0
    m, n = len(matrix), len(matrix[0])

    dp = [[0]* n for _ in range(m)]

    max_size=0

    for i in range(m):
        for j in range(n):
            if matrix[i][j] =='1':
                if i ==0 or j == 0:
                    dp[i][j]=1
                else:
                    dp[i][j] = min(dp[i-1][j],dp[i-1][j-1],dp[i][j-1])+1
                max_size= max(max_size,dp[i,j])
    return max_size**2



def remove_element_in_place(nums:List[int], val:int)->int:
    k=0
    for i in range(len(nums)-1,-1,-1):
        if nums[i]==val:
            del nums[i]
            nums.append(0)
        else:
            k+=1
    return k

remove_element_in_place([0,1,2,2,3,0,4,2],val=2)




def removeDuplicates(nums:List[int])->int:
    if len(nums)==1:
        return 1
    k=0
    for i in range(len(nums)):
        flag=True
        while flag:
            if nums[i+1]=="_":
                return k+1
            if nums[i]==nums[i+1]:
                del nums[i+1]
                nums.append('_')
            else:
                k+=1
                flag=False
                nums.append('_')
    
print(removeDuplicates([1,1,2]))
print(removeDuplicates([0,0,1,1,1,2,2,3,3,4]))


def remove_duplicates_up_to_2(nums:List[int])->int:
    j=1
    for i in range(1,len(nums)):
        if j==1 or nums[i] != nums[j-2]:
            nums[j] = nums[i]
            j +=1
    return j
    
print(remove_duplicates_up_to_2([0,0,1,1,1,2,2,3,3,4]))

        
def majority_element(nums:list[int])-> int:
    """
    Given an array nums of size n, return the majority element.
    The majority element is the element that appears more than ⌊n / 2⌋ times. You may assume that the majority element always exists in the array.
    """
    majority_candidate = nums[0]
    count=1
    for i in range(1,len(nums)):
        if majority_candidate == nums[i]:
            count +=1
        else:
            count -=1
        if count==0:
            majority_candidate= nums[i+1]
    return majority_candidate

majority_element([2,2,1,1,1,2,2])


    


    
def maxProfit(prices: List[int]) -> int:
        profit=0
        buy_flag=False
        for i in range(len(prices)):
            if i == len(prices)-1:
                if buy_flag is True:
                    return profit + (prices[i]-buy)
                else:
                    return profit
            # lets say we don't have the stock
            if buy_flag is False:
                # is the price from the next day higher?
                if prices[i+1] > prices[i]:
                    # we buy
                    buy=prices[i]
                    buy_flag=True
            else:
                # We have bought a stock
                # if the profit from the next day is lower, we sell
                if (prices[i+1] - buy) < (prices[i]-buy):
                    buy_flag=False
                    profit += prices[i]-buy

maxProfit([7,1,5,3,6,4])


def canJump(nums: List[int]) -> bool:
    goal=len(nums)-1
    current_position=len(nums)-2
    while current_position !=-1:
        if current_position + nums[current_position] >= goal:
            goal = current_position
            current_position -=1
            continue
        else:
            current_position -=1
    return goal==0

canJump([2,3,1,1,4])
canJump([3,2,1,0,4])

def jump(nums: List[int]) -> bool:
    goal=len(nums)-1
    max_jump = 1000
    k=0
    while goal != 0:
        for i in range(goal-1,max(-1,(goal-max_jump-1)),-1):
            if i + nums[i] >= goal:
                candidate= i 
        goal=candidate
        k+=1
    return k

def jump(nums: List[int]) -> int:
    ans = 0
    curr_end,curr_far = 0,0
    for i in range(len(nums)-1):
        curr_far = max(curr_far,i+nums[i])
        if i==curr_end:
            ans+=1
            curr_end = curr_far

    return ans

jump([2,3,1,1,4])
jump([2,3,0,1,4])


def hIndex(citations: List[int]) -> int:
    h_index =0 
    citations.sort()
    for i in range(len(citations)-1,-1,-1):
        candidate = min(len(citations[i:]),citations[i])
        if candidate > h_index:
            h_index=candidate
    return h_index

hIndex([3,0,6,1,5])

import random
class RandomizedSet:

    def __init__(self):
        self.dict = {}
        self.val_list=[]

    def insert(self, val: int) -> bool:
        if self.dict.get(val,None) is not None:
            return False
        else:
            self.val_list.append(val)
            self.dict[val]= len(self.val_list)-1
            return True
        
    def remove(self, val: int) -> bool:
        # If exists
        if self.dict.get(val,None) is not None :
            # get the position where the val is in the list
            position = self.dict[val]
            # Place the last element in the list to the position of val
            self.val_list[position] = self.val_list[len(self.val_list)-1]
            # update the dictionary
            self.dict[self.val_list[len(self.val_list)-1]] = position
            # remove the last element of the list
            self.val_list.pop()
            # remove the entry from the dictionary
            del self.dict[val]
            return True
        else:
            return False
        
    def getRandom(self) -> int:
        return random.choice(self.val_list)

rando_set = RandomizedSet()
rando_set.insert(32)
rando_set.insert(34)
rando_set.insert(36)
print(rando_set.getRandom())
rando_set.insert(32)
print(rando_set.getRandom())
rando_set.remove(32)
print(rando_set.getRandom())
rando_set.remove(33)

    
def productExceptSelf(nums: List[int]) -> List[int]:
    left_list= [1] * len(nums)
    right_list= [1] * len(nums)
    for i in range(1,len(nums)):
        left_list[i]=left_list[i-1]*nums[i-1]
    for i in range (len(nums)-2,-1,-1):
        right_list[i]=right_list[i+1]*nums[i+1]
    return [left_list[i] * right_list[i] for i in range(len(nums))]



productExceptSelf([1,2,3,4])
productExceptSelf([-1,1,0,-3,3])

def canCompleteCircuit(gas: List[int], cost: List[int]) -> int:
    n, total_surplus, surplus, start = len(gas), 0, 0, 0
    for i in range(n):
        total_surplus += gas[i] - cost[i]
        surplus += gas[i] - cost[i]
        if surplus < 0:
            surplus = 0
            start = i + 1
    return -1 if (total_surplus < 0) else start

        

canCompleteCircuit( gas = [1,2,3,4,5], cost = [3,4,5,1,2])
canCompleteCircuit(gas = [2,3,4], cost = [3,4,3])
                

def candy(ratings: List[int]) -> int:
    candies = [1] * len(ratings)
    for i in range(1,len(ratings)):
        # compare to the left
        if (ratings[i] > ratings[i-1]):
            candies[i] = candies[i-1]+1
    for i in range(len(ratings)-2,-1,-1):
        # comparte to the right
        if (ratings[i] > ratings[i+1]):
            candies[i] = candies[i+1]+1
    return sum(candies)
    
candy([1,2,87,87,87,2,1])


def trap(height: List[int]) -> int:
    # generate the max to the left
    n=len(height)
    left_max = [0] * n
    right_max = [0] * n
    water=[0]*n
    for i in range(1,n):
        left_max[i] = max(left_max[i-1],height[i-1])
    for i in range(n-2,-1,-1):
        right_max[i] = max(right_max[i+1],height[i+1])

    for i in range(n):
        water[i]= max(0,min(left_max[i],right_max[i])-height[i])
    return sum(water)



trap([0,1,0,2,1,0,1,3,2,1,2,1])


def romanToInt(s: str) -> int:
    roman_values={
        "I":1,
        "V":5,
        "X":10,
        "L":50,
        "C":100,
        "D":500,
        "M":1000
    }
    n= len(s)
    max_unit=0
    number=0
    for i in range(n-1,-1,-1):
        max_unit = max(roman_values[s[i]],max_unit)
        if roman_values[s[i]] == max_unit:
            number += roman_values[s[i]]
        else:
            number -= roman_values[s[i]]
    return number

romanToInt("MCMXCIV")

def intToRoman(num: int) -> str:
    Roman = ""
    storeIntRoman = [[1000, "M"], [900, "CM"], [500, "D"], [400, "CD"], [100, "C"], [90, "XC"], [50, "L"], [40, "XL"], [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]]
    for i in range(len(storeIntRoman)):
        while num >= storeIntRoman[i][0]:
            Roman += storeIntRoman[i][1]
            num -= storeIntRoman[i][0]
    return Roman

    
def lengthOfLastWord(s: str) -> int:
    n=len(s)
    word_started=False
    word_length=0
    for i in range(n-1,-1,-1):
        if s[i] ==" ":
            if word_started==True:
                return word_length
        else:
            word_started=True
            word_length+=1
            if i==0:
                return word_length

lengthOfLastWord("a ")
lengthOfLastWord("luffy is still joyboy")
lengthOfLastWord("Hello World")
lengthOfLastWord("   fly me   to   the moon  ")


        
def longestCommonPrefix(strs: List[str]) -> str:
    prefix=""
    j=0
    n = len(strs)
    while True:
        for i in range(1,n):
            if j > len(strs[i])-1:
                return prefix
            if strs[i][j] != strs[i-1][j]:
                return prefix
        prefix = prefix+strs[i][j]
        j+=1
        
longestCommonPrefix(["dog","racecar","car"])
longestCommonPrefix(["flower","flow","flight"])
            
def reverseWords( s: str) -> str:
    x=s.split()
    string = " ".join(x[::-1])
    return string

reverseWords("  hello world  ")
reverseWords( "the sky is blue")


def convert(s: str, numRows: int) -> str:
    places=[[] for _ in range(numRows)]
    i=0
    direction = "up"
    for character in s:
        places[i].append(character)
        if (i < numRows-1) & (direction == "up"):
            i+=1
        elif (i ==0) & (direction == "down"):
            direction= "up"
            i+=1
        else:
            i-=1
            direction="down"
    complete_string = "".join( [x for xs in places for x in xs ])
    return complete_string
        
        
convert("PAYPALISHIRING",3)

            








        

