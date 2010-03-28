#! /usr/bin/env ruby
phases = ARGV.empty? ? %w{tagged binarised labelled fixed_rc fixed_adverbs fixed_np} : ARGV

STDIN.each {|line|
    line.chomp!
    
    (line =~ /(\d+):(\d+)\((\d+)\)/) || (line =~ /(\d+),(\d+),(\d+)/)
    doc_name = "chtb_%02d%02d.fid" % [$1, $2]
    pdf_name = "wsj_%02d%02d.%02d.pdf" % [$1, $2, $3]
    section_name = "%02d" % $1
    
    `./make_all.sh #{doc_name}`
    phases.each {|phase|
        if ["tagged", "binarised"].include? phase
            `./t -q -D #{phase}_dots #{phase}/#{doc_name}:#{$3} 2>&1`
        else
            `./t -q -D #{phase}_dots -R AugmentedPTBReader #{phase}/#{doc_name}:#{$3} 2>&1`
        end
        
        `open #{phase}_dots/#{section_name}/#{pdf_name}`
    }
}
