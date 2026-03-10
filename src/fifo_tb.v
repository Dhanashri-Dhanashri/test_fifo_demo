//testbench for fifo
`timescale 1ns/1ns

module test;

  parameter FIFO_DEPTH = 8;
  parameter DATA_WIDTH = 8; 

  reg                   Clock;
  reg                   Reset_;
  reg                   WriteEn;
  reg                   ReadEn;
  reg  [DATA_WIDTH-1:0] DataIn;
  wire [DATA_WIDTH-1:0] DataOut;
  wire                  FifoEmpty;
  wire                  FifoHalfFull;
  wire                  FifoFull;
  wire                  Error;

//`begin_faultfree
  FIFO #(.FIFO_DEPTH(FIFO_DEPTH), .DATA_WIDTH(DATA_WIDTH)) DUT 
  (
    .Reset_(Reset_),
    .ReadClk(Clock),
    .WriteClk(Clock),
    .WriteEn(WriteEn),
    .DataIn(DataIn),
    .ReadEn(ReadEn),
    .DataOut(DataOut),
    .Empty_(FifoEmpty),
    .HalfFull_(FifoHalfFull),
    .Full_(FifoFull),
    .Error(Error)
  ); 
//`end_faultfree

  initial
    begin
      Clock = 1'b0;
      forever
        #50 Clock = ~Clock;
   end

  task FifoTransfer;
    input                  Write;
    input [DATA_WIDTH-1:0] WData;
    input                  Read;
    input [DATA_WIDTH-1:0] ExpectedData;
    begin
      if (Write)
        $display("Write %h", WData);
      WriteEn <= Write;
      ReadEn  <= Read;
      DataIn  <= WData;
      @(negedge Clock);
      if (Read === 1'b1)
        begin
          if (DataOut !== ExpectedData)
            begin
              $display($time,": FAIL: got %h, was expecting %h\n", DataOut, ExpectedData);
              //$finish;
            end
          $display("Read %h", DataOut);
        end
      #10; 
      WriteEn <= 1'b0;
      ReadEn  <= 1'b0;
    end
   endtask

  task CheckFlags;
    input Empty;
    input HalfFull;
    input Full;
    begin
      if (FifoEmpty !== Empty)
        begin
          $display($time,": FAIL: wrong 'Empty' flag value, got %h, was expecting %h\n", FifoEmpty, Empty);
          //$finish;
        end
      if (FifoHalfFull !== HalfFull)
        begin
          $display($time,": FAIL: wrong 'HalfFull' flag value, got %h, was expecting %h\n", FifoHalfFull, HalfFull);
          //$finish;
        end
      if (FifoFull !== Full)
        begin
          $display($time,": FAIL: wrong 'Full' flag value, got %h, was expecting %h\n", FifoFull, Full);
          //$finish;
        end
      $display("Check Flags - PASS");
    end
  endtask

  integer i;

  initial
    begin
      // Initialize Memory
      for (int i=0; i < FIFO_DEPTH; i++)
      begin
         #1 test.DUT.sdpram_i1.sdpram_i1.mem_array[i] <= {DATA_WIDTH{1'b0}};
      end
      
      if($test$plusargs("test1"))
      begin
        `include "./testcases/test1.v"
      end
      if($test$plusargs("test2"))
      begin
        `include "./testcases/test2.v"
      end
      $display("Calling finish");
      #10 $finish;
    end

  // ----------------------------
  // Minimal fault-injection hooks
  // ----------------------------
  integer fi_time;
  integer fi_mem_addr;
  integer fi_mem_bit;
  integer fi_mem_stuck;
  integer fi_rp_bit;
  integer fi_wp_bit;
  integer fi_flag_bit;

`ifdef USE_SDPRAM_TOP
  localparam MEM_WIDTH = DATA_WIDTH + 4;
`else
  localparam MEM_WIDTH = DATA_WIDTH;
`endif

  task InjectMemBitFlip;
    input integer addr;
    input integer bit_idx;
    begin
`ifdef USE_SDPRAM_TOP
      $display($time,": FI: mem flip addr=%0d bit=%0d (SDPRAM_TOP)", addr, bit_idx);
      test.DUT.sdpram_i1.sdpram_i1.mem_array[addr][bit_idx] <=
        ~test.DUT.sdpram_i1.sdpram_i1.mem_array[addr][bit_idx];
`else
      $display($time,": FI: mem flip addr=%0d bit=%0d (SDPRAM)", addr, bit_idx);
      test.DUT.sdpram_i1.mem_array[addr][bit_idx] <=
        ~test.DUT.sdpram_i1.mem_array[addr][bit_idx];
`endif
    end
  endtask

  task InjectMemBitStuck;
    input integer addr;
    input integer bit_idx;
    input integer stuck_val;
    reg [MEM_WIDTH-1:0] tmp;
    begin
`ifdef USE_SDPRAM_TOP
      $display($time,": FI: mem stuck addr=%0d bit=%0d val=%0d (SDPRAM_TOP)", addr, bit_idx, stuck_val);
      tmp = test.DUT.sdpram_i1.sdpram_i1.mem_array[addr];
      tmp[bit_idx] = stuck_val[0];
      force test.DUT.sdpram_i1.sdpram_i1.mem_array[addr] = tmp;
`else
      $display($time,": FI: mem stuck addr=%0d bit=%0d val=%0d (SDPRAM)", addr, bit_idx, stuck_val);
      tmp = test.DUT.sdpram_i1.mem_array[addr];
      tmp[bit_idx] = stuck_val[0];
      force test.DUT.sdpram_i1.mem_array[addr] = tmp;
`endif
    end
  endtask

  task InjectReadPtrBitFlip;
    input integer bit_idx;
    begin
`ifdef USE_SAFETY_DESIGN
      $display($time,": FI: read ptr bit flip bit=%0d (RP_IF)", bit_idx);
      test.DUT.RP_IF.Count[bit_idx] <= ~test.DUT.RP_IF.Count[bit_idx];
`else
      $display($time,": FI: read ptr bit flip bit=%0d (RP)", bit_idx);
      test.DUT.RP.Count[bit_idx] <= ~test.DUT.RP.Count[bit_idx];
`endif
    end
  endtask

  task InjectWritePtrBitFlip;
    input integer bit_idx;
    begin
`ifdef USE_SAFETY_DESIGN
      $display($time,": FI: write ptr bit flip bit=%0d (WP_IF)", bit_idx);
      test.DUT.WP_IF.Count[bit_idx] <= ~test.DUT.WP_IF.Count[bit_idx];
`else
      $display($time,": FI: write ptr bit flip bit=%0d (WP)", bit_idx);
      test.DUT.WP.Count[bit_idx] <= ~test.DUT.WP.Count[bit_idx];
`endif
    end
  endtask

  task InjectFlagCountBitFlip;
    input integer bit_idx;
    begin
`ifdef USE_SAFETY_DESIGN
      $display($time,": FI: flag count bit flip bit=%0d (FL_IF)", bit_idx);
      test.DUT.FL_IF.Count[bit_idx] <= ~test.DUT.FL_IF.Count[bit_idx];
`else
      $display($time,": FI: flag count bit flip bit=%0d (FL)", bit_idx);
      test.DUT.FL.Count[bit_idx] <= ~test.DUT.FL.Count[bit_idx];
`endif
    end
  endtask

  initial begin
    if (!$value$plusargs("FI_TIME=%d", fi_time)) fi_time = 150;

    if ($value$plusargs("FI_MEM_ADDR=%d", fi_mem_addr) &&
        $value$plusargs("FI_MEM_BIT=%d", fi_mem_bit)) begin
      #fi_time;
      if ($value$plusargs("FI_MEM_STUCK=%d", fi_mem_stuck))
        InjectMemBitStuck(fi_mem_addr, fi_mem_bit, fi_mem_stuck);
      else
        InjectMemBitFlip(fi_mem_addr, fi_mem_bit);
    end

    if ($value$plusargs("FI_RP_BIT=%d", fi_rp_bit)) begin
      #fi_time;
      InjectReadPtrBitFlip(fi_rp_bit);
    end

    if ($value$plusargs("FI_WP_BIT=%d", fi_wp_bit)) begin
      #fi_time;
      InjectWritePtrBitFlip(fi_wp_bit);
    end

    if ($value$plusargs("FI_FLAG_BIT=%d", fi_flag_bit)) begin
      #fi_time;
      InjectFlagCountBitFlip(fi_flag_bit);
    end
  end

/*
  initial
    $fsdbDumpvars;
*/

endmodule
