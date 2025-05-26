# debug.py
import sys
import langchain_core
import langchain_core.output_parsers

print("="*30)
print("PYTHON EXECUTABLE:")
print(sys.executable)
print("="*30)

print("\n" + "="*30)
print("PYTHON SYS.PATH:")
for p in sys.path:
    print(p)
print("="*30)


print("\n" + "="*30)
print("LANGCHAIN_CORE LOCATION:")
print(langchain_core.__file__)
print("="*30)

print("\n" + "="*30)
print("LANGCHAIN_CORE.OUTPUT_PARSERS LOCATION:")
print(langchain_core.output_parsers.__file__)
print("="*30)

print("\n" + "="*30)
print("CONTENTS OF LANGCHAIN_CORE.OUTPUT_PARSERS:")
print(dir(langchain_core.output_parsers))
print("="*30)

print("\n" + "="*30)
print("IS 'StringOutputParser' IN THERE? -->", 'StringOutputParser' in dir(langchain_core.output_parsers))
print("="*30)