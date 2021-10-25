CC = gcc
CFLAGS = -g -Wall
LFLAGS = -lhwloc

TARGET = topology
OUTPUT = test.rec

all: $(TARGET)

$(TARGET): $(TARGET).c
	$(CC) $(CFLAGS) -o $(TARGET) $(TARGET).c $(LFLAGS)

clean:
	$(RM) $(TARGET) $(OUTPUT)

