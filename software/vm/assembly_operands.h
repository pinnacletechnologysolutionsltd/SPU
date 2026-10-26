#ifndef SPU_ASSEMBLY_OPERANDS_H
#define SPU_ASSEMBLY_OPERANDS_H
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#include <cctype>

// Source-only validation. Raw instruction decoding is deliberately unchanged.
static long long operand_integer(const std::string& token) {
    size_t used = 0;
    size_t sign = (!token.empty() && (token[0]=='-' || token[0]=='+')) ? 1 : 0;
    int base = token.size()>sign+2 && (token.substr(sign,2)=="0x" || token.substr(sign,2)=="0X") ? 16 : 10;
    long long value = std::stoll(token, &used, base);
    if (used!=token.size()) throw std::runtime_error("invalid integer: "+token);
    return value;
}
static int operand_register(std::string token, char kind=0) {
    for (auto& c:token) c=static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    bool qr=token.substr(0,2)=="QR";
    size_t start=qr ? 2 : 1;
    if ((!qr && token.substr(0,1)!="R") || token.size()<=start)
        throw std::runtime_error("invalid register: "+token);
    for (size_t i=start;i<token.size();++i)
        if (!std::isdigit(static_cast<unsigned char>(token[i])))
            throw std::runtime_error("invalid register: "+token);
    int index=std::stoi(token.substr(start));
    if ((kind=='Q' && !qr) || (kind=='R' && qr))
        throw std::runtime_error("wrong register type: "+token);
    if (index>(qr ? 12 : 25)) throw std::runtime_error("register out of range: "+token);
    return index;
}
static void validate_operands(const std::vector<std::string>& parts,
                             const std::unordered_map<std::string,int>& labels) {
    static const std::unordered_map<std::string,std::string> kinds={
        {"LD","RII"},{"ADD","RR"},{"SUB","RR"},{"MUL","RR"},
        {"ROT","RR"},{"LOG","R"},{"JINV","R"},{"JMP","L"},{"CALL","L"},
        {"QLOAD","QR"},{"QADD","QQ"},{"QREAD","QQ"},{"QSUB","QQQ"},
        {"QROT","QR"},{"ROTC","QQI"},{"QLDI","QIIII"},{"DELTA","QIII"},
        {"HEX","RQ"},{"SPREAD","RQQ"},{"QLOG","Q"},{"QNORM","Q"},
        {"IDNT","Q"},{"ANNE","Q"},{"NOP",""},{"HALT",""},
        {"RET",""},{"SNAP",""},{"EQUIL",""}};
    std::string m=parts[0];
    for (auto& c:m) c=static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    auto found=kinds.find(m);
    if (found==kinds.end()) throw std::runtime_error("unreviewed operand grammar: "+m);
    const auto& pattern=found->second;
    size_t count=parts.size()-1, minimum=pattern.size(), maximum=minimum;
    if (m=="LD") minimum=1;
    if (m=="ROT" || m=="QROT") minimum=1;
    if (m=="QSUB") minimum=2;
    if (count<minimum || count>maximum) throw std::runtime_error("invalid operand count: "+m);
    for (size_t i=0;i<count;++i) {
        std::string token=parts[i+1];
        for (auto& c:token) c=static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        char kind=pattern[i];
        if (kind=='Q' || kind=='R') operand_register(token,kind);
        else if (kind=='L' && labels.count(token)) continue;
        else {
            auto value=operand_integer(parts[i+1]);
            if (kind=='L' && (value<0 || value>65535))
                throw std::runtime_error("control destination out of range");
        }
    }
    if (m=="QLOAD" && operand_register(parts[2],'R')>22)
        throw std::runtime_error("QLOAD needs four consecutive registers");
    if (m=="ROTC" && (operand_integer(parts[3])<0 || operand_integer(parts[3])>63))
        throw std::runtime_error("ROTC selector out of range");
}
#endif
