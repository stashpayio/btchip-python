"""
*******************************************************************************
*   BTChip Bitcoin Hardware Wallet Python API
*   (c) 2014 BTChip - 1BTChip7VfTnrPra5jqci7ejnMguuHogTn
*
*  Licensed under the Apache License, Version 2.0 (the "License");
*  you may not use this file except in compliance with the License.
*  You may obtain a copy of the License at
*
*      http://www.apache.org/licenses/LICENSE-2.0
*
*   Unless required by applicable law or agreed to in writing, software
*   distributed under the License is distributed on an "AS IS" BASIS,
*   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*  See the License for the specific language governing permissions and
*   limitations under the License.
********************************************************************************
"""

from .bitcoinVarint import *
from binascii import hexlify

class bitcoinInput:

	def __init__(self, bufferOffset=None):
		self.prevOut = b""
		self.script = b""
		self.sequence = b""
		if bufferOffset is not None:
			buf = bufferOffset['buffer']
			offset = bufferOffset['offset']
			self.prevOut = buf[offset:offset + 36]
			offset += 36
			scriptSize = readVarint(buf, offset)
			offset += scriptSize['size']
			self.script = buf[offset:offset + scriptSize['value']]
			offset += scriptSize['value']
			self.sequence = buf[offset:offset + 4]
			offset += 4
			bufferOffset['offset'] = offset

	def serialize(self):
		result = []
		result.extend(self.prevOut)
		writeVarint(len(self.script), result)
		result.extend(self.script)
		result.extend(self.sequence)
		return result

	def __str__(self):
		buf = "Prevout : " + self.prevOut.hex() + "\r\n"
		buf += "Script : " + self.script.hex() + "\r\n"
		buf += "Sequence : " + self.sequence.hex() + "\r\n"
		return buf

class bitcoinOutput:

	def __init__(self, bufferOffset=None):
		self.amount = b""
		self.script = b""
		if bufferOffset is not None:
			buf = bufferOffset['buffer']
			offset = bufferOffset['offset']
			self.amount = buf[offset:offset + 8]
			offset += 8
			scriptSize = readVarint(buf, offset)
			offset += scriptSize['size']
			self.script = buf[offset:offset + scriptSize['value']]
			offset += scriptSize['value']
			bufferOffset['offset'] = offset

	def serialize(self):
		result = []
		result.extend(self.amount)
		writeVarint(len(self.script), result)
		result.extend(self.script)
		return result

	def __str__(self):
		buf = "Amount : " + self.amount.hex() + "\r\n"
		buf += "Script : " + self.script.hex() + "\r\n"
		return buf


class bitcoinTransaction:

	def __init__(self, data=None):
		self.version = b""
		self.inputs = []
		self.outputs = []
		self.lockTime = b""
		self.witness = False
		self.witnessScript = b""
		self.extra_data = b"\x00"
		if data is not None:
			offset = 0
			self.version = data[offset:offset + 4]
			offset += 4
			#if (data[offset] == 0) and (data[offset + 1] != 0):
			#	offset += 2
			#	self.witness = True
			inputSize = readVarint(data, offset)
			offset += inputSize['size']
			numInputs = inputSize['value']
			for i in range(numInputs):
				tmp = { 'buffer': data, 'offset' : offset}
				self.inputs.append(bitcoinInput(tmp))
				offset = tmp['offset']
			outputSize = readVarint(data, offset)
			offset += outputSize['size']
			numOutputs = outputSize['value']
			for i in range(numOutputs):
				tmp = { 'buffer': data, 'offset' : offset}
				self.outputs.append(bitcoinOutput(tmp))
				offset = tmp['offset']
			if self.witness:
				self.witnessScript = data[offset : len(data) - 4]
				self.lockTime = data[len(data) - 4:]
			else:
				self.lockTime = data[offset:offset + 4]
				offset+=4
			# Read any extra data
			bytesRemaining = len(data) - offset
			if bytesRemaining > 0:
				self.extra_data = data[offset : offset + bytesRemaining]		
			
	def serialize(self, skipOutputLocktime=False, skipWitness=False):
		if skipWitness or (not self.witness):
			useWitness = False
		else:
			useWitness = True
		result = []
		result.extend(self.version)
		if useWitness:
			result.append(0x00)
			result.append(0x01)
		writeVarint(len(self.inputs), result)
		for trinput in self.inputs:
			result.extend(trinput.serialize())
		if not skipOutputLocktime:
			writeVarint(len(self.outputs), result)
			for troutput in self.outputs:
				result.extend(troutput.serialize())
			if useWitness:
				result.extend(self.witnessScript)
			result.extend(self.lockTime)
		if int.from_bytes(self.version, byteorder='little') < 3 and self.extra_data:
			result.extend(self.extra_data)
		return result

	def serializeOutputs(self):
		result = []
		writeVarint(len(self.outputs), result)
		for troutput in self.outputs:
			result.extend(troutput.serialize())
		return result

	def __str__(self):
		buf = "Version : " + self.version.hex() + "\r\n"
		index = 1
		for trinput in self.inputs:
			buf += "Input #" + str(index) + "\r\n"
			buf += str(trinput)
			index+=1
		index = 1
		for troutput in self.outputs:
			buf += "Output #" + str(index) + "\r\n"
			buf += str(troutput)
			index+=1
		buf += "Locktime : " + self.lockTime.hex() + "\r\n"
		if self.witness:
			buf += "Witness script : " + self.witnessScript.hex() + "\r\n"
		if self.extra_data:
			buf += "Extra data :" + self.extra_data.hex() + "\r\n"
		return buf
