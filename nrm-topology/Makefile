CC = gcc
CFLAGS = -Wall
LFLAGS = -lhwloc

TARGET = topology

all: $(TARGET)

$(TARGET): $(TARGET).c
	$(CC) $(CFLAGS) -o $(TARGET) $(TARGET).c $(LFLAGS)

clean:
	$(RM) $(TARGET) $(OUTPUT)

