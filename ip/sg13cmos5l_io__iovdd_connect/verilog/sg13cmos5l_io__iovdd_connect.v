// Copyright 2024 IHP PDK Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// type: sg13cmos5l_io__iovdd_connect
`timescale 1ns/10ps
`celldefine
//*****************************************************************
//   technology       : sg13cmos5l
//   module name      : sg13cmos5l_io__iovdd_connect
//   cell_description : Provides a core connection for iovdd, width 5 um.
//*****************************************************************
(* blackbox *)
module sg13cmos5l_io__iovdd_connect (vdd, vss, iovdd, iovss);
	inout vdd;
	inout vss;	
	inout iovdd;
	inout iovss;
endmodule
`endcelldefine
