      $display("Reset");
      Reset_ = 1'b0;
      ReadEn = 1'b0;
      WriteEn = 1'b0;
      #220
      Reset_ = 1'b1;

      // Reset flags check
      CheckFlags(.Empty(1'b0), .HalfFull(1'b1), .Full(1'b1));

      @(negedge Clock);

      // Write FIFO until full

      FifoTransfer(.Write(1'b1), .WData(8'h0), .Read(1'b0), .ExpectedData(8'hx));
      // Empty flag check
      CheckFlags(.Empty(1'b1), .HalfFull(1'b1), .Full(1'b1));

      FifoTransfer(.Write(1'b1), .WData(8'h1), .Read(1'b0), .ExpectedData(8'hx));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b1), .Full(1'b1));

      FifoTransfer(.Write(1'b1), .WData(8'h2), .Read(1'b0), .ExpectedData(8'hx));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b1), .Full(1'b1));

      FifoTransfer(.Write(1'b1), .WData(8'h3), .Read(1'b0), .ExpectedData(8'hx));
      // HalfFull flag check
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b1));

      FifoTransfer(.Write(1'b1), .WData(8'h4), .Read(1'b0), .ExpectedData(8'hx));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b1));

      FifoTransfer(.Write(1'b1), .WData(8'h5), .Read(1'b0), .ExpectedData(8'hx));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b1));

      FifoTransfer(.Write(1'b1), .WData(8'h6), .Read(1'b0), .ExpectedData(8'hx));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b1));

      FifoTransfer(.Write(1'b1), .WData(8'h7), .Read(1'b0), .ExpectedData(8'hx));
      // Full flag
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b0));

      // Check FIFO will not write when full
      FifoTransfer(.Write(1'b1), .WData(8'h8), .Read(1'b0), .ExpectedData(8'bx)); 
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b0));

      // Read FIFO until empty

      FifoTransfer(.Write(1'b0), .WData(8'hx), .Read(1'b1), .ExpectedData(8'h0));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b1));

      FifoTransfer(.Write(1'b0), .WData(8'hx), .Read(1'b1), .ExpectedData(8'h1));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b1));

      FifoTransfer(.Write(1'b0), .WData(8'hx), .Read(1'b1), .ExpectedData(8'h2));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b1));

      FifoTransfer(.Write(1'b0), .WData(8'hx), .Read(1'b1), .ExpectedData(8'h3));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b1));

      FifoTransfer(.Write(1'b0), .WData(8'hx), .Read(1'b1), .ExpectedData(8'h4));
      // HalfFull flag check
      CheckFlags(.Empty(1'b1), .HalfFull(1'b1), .Full(1'b1));

      FifoTransfer(.Write(1'b0), .WData(8'hx), .Read(1'b1), .ExpectedData(8'h5));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b1), .Full(1'b1));

      FifoTransfer(.Write(1'b0), .WData(8'hx), .Read(1'b1), .ExpectedData(8'h6));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b1), .Full(1'b1));

      FifoTransfer(.Write(1'b0), .WData(8'hx), .Read(1'b1), .ExpectedData(8'h7));
      // Empty flag check
      CheckFlags(.Empty(1'b0), .HalfFull(1'b1), .Full(1'b1));

      // Check FIFO will not read when empty
      FifoTransfer(.Write(1'b0), .WData(8'hx), .Read(1'b1), .ExpectedData(8'h7));
      CheckFlags(.Empty(1'b0), .HalfFull(1'b1), .Full(1'b1));

      // Check simultaneous read/write

      FifoTransfer(.Write(1'b1), .WData(8'h8), .Read(1'b0), .ExpectedData(8'hx));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b1), .Full(1'b1));
      FifoTransfer(.Write(1'b1), .WData(8'h9), .Read(1'b1), .ExpectedData(8'h8));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b1), .Full(1'b1));
      FifoTransfer(.Write(1'b0), .WData(8'hx), .Read(1'b1), .ExpectedData(8'h9));
      CheckFlags(.Empty(1'b0), .HalfFull(1'b1), .Full(1'b1));

      // Check HalfFull flag
      FifoTransfer(.Write(1'b1), .WData(8'ha), .Read(1'b0), .ExpectedData(8'hx));
      FifoTransfer(.Write(1'b1), .WData(8'hb), .Read(1'b0), .ExpectedData(8'hx));
      FifoTransfer(.Write(1'b1), .WData(8'hc), .Read(1'b0), .ExpectedData(8'hx));
      FifoTransfer(.Write(1'b1), .WData(8'hd), .Read(1'b0), .ExpectedData(8'hx));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b1));

      FifoTransfer(.Write(1'b1), .WData(8'he), .Read(1'b1), .ExpectedData(8'ha));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b1));

      FifoTransfer(.Write(1'b1), .WData(8'hf), .Read(1'b1), .ExpectedData(8'hb));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b1));

      FifoTransfer(.Write(1'b1), .WData(8'h0), .Read(1'b0), .ExpectedData(8'hx));
      CheckFlags(.Empty(1'b1), .HalfFull(1'b0), .Full(1'b1));

      $display("Test done\n");
      $finish;
