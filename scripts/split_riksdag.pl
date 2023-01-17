#!/usr/bin/perl
# Copyright (c) 2022, Jim O'Regan for Språkbanken Tal
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

use warnings;
use strict;
use utf8;

binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");

my $prev = '';
my $counter = 0;

while(<>) {
    chomp;
    my @p = split/_/;
    if ($prev eq '' || $prev ne $p[0])  {
        my $file = "outdir/" . $p[0] . ".txt";
        if ($prev ne '') {
            close FH;
        }
        open(FH, ">", $file);
        binmode(FH, ":utf8");
        $prev = $p[0];
        $counter = 0;
    }
    my @parts = split/ /;
    shift(@parts);

    print FH $prev . "_" . $counter . " " . join(" ", @parts) . "\n";
    $counter++;
}