# strip_claude_trailers.pl -- git filter-branch --msg-filter helper.
# Removes "Co-Authored-By: Claude ..." and "Claude-Session: ..." lines from a commit message on stdin
# and collapses the trailing blank lines they leave behind.
local $/; my $m = <STDIN>;
$m =~ s/^(Co-Authored-By: Claude[^\n]*|Claude-Session:[^\n]*)\n?//mg;
$m =~ s/\n{3,}/\n\n/g;
$m =~ s/\s+\z/\n/;
print $m;
