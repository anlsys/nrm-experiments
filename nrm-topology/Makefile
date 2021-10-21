CC = gcc
CFLAGS = -Wall
LFLAGS = -lhwloc

TARGET = topology
OUTPUT = test.log

all: $(TARGET)

$(TARGET): $(TARGET).c
	$(CC) $(CFLAGS) -o $(TARGET) $(TARGET).c $(LFLAGS)

clean:
	$(RM) $(TARGET) $(OUTPUT)

