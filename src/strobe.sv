`timescale 1ns/1ns

module strobe;

initial
begin
  $fsdbDumpvars;
end


  integer cmp;

  initial
    begin
			@(posedge test.Reset_)
      $fs_inject;
      forever @(negedge test.Clock)
        begin
          #20
          cmp = $fs_compare(test.DUT.DataOut, test.DUT.Empty_, test.DUT.HalfFull_, test.DUT.Full_);
          if (1 == cmp)
            $fs_set_status("ON");
          else if (2 == cmp)
            $fs_set_status("PN");
        end
    end

  string status;

  initial
    begin
			@(posedge test.Reset_)
      forever @(negedge test.Clock)
        begin
          #30
          cmp = $fs_compare(test.DUT.Error);
          status = $fs_get_status();
          if (1 == cmp)
            begin
              if (status == "ON")
                $fs_drop_status("OD");
              else if (status == "PN")
                $fs_drop_status("PD");
              else
                $fs_set_status("ND");
            end
          else if (2 == cmp)
            begin
              if (status == "ON")
                $fs_drop_status("OP");
              else if (status == "PN")
                $fs_drop_status("PP");
              else
                $fs_set_status("NP");
            end
        end
    end

endmodule
